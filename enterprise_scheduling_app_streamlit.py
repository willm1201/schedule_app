# app.py
# Enterprise-grade Scheduling App with Recurring Events (Streamlit Cloud Ready)

import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import uuid

st.set_page_config(
    page_title="Enterprise Scheduler",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------
# Styling – Corporate Polish
# --------------------

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .metric-container {
        background-color: #f7f9fc;
        border-radius: 12px;
        padding: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------
# Utilities
# --------------------

def generate_id():
    return str(uuid.uuid4())

if "events" not in st.session_state:
    st.session_state.events = pd.DataFrame(columns=[
        "id", "series_id", "title", "owner", "start", "end",
        "priority", "status", "recurrence", "notes"
    ])

# --------------------
# Sidebar
# --------------------

st.sidebar.title("Enterprise Scheduler")
st.sidebar.caption("Operational Scheduling Platform")
view = st.sidebar.radio("Navigation", [
    "Create Event",
    "Event List",
    "Calendar View",
    "Admin Dashboard"
])

# --------------------
# Create Event
# --------------------

if view == "Create Event":
    st.title("Create Schedule")
    st.caption("Define one-time or recurring operational events")

    with st.form("create_event_form"):
        title = st.text_input("Event Title")
        owner = st.text_input("Owner / Team")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today())
            start_time = st.time_input("Start Time", time(9, 0))
        with col2:
            end_date = st.date_input("End Date", date.today())
            end_time = st.time_input("End Time", time(10, 0))

        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        status = st.selectbox("Status", ["Planned", "Confirmed"])

        recurrence = st.selectbox(
            "Recurrence",
            ["None", "Daily", "Weekly", "Monthly"]
        )

        occurrences = st.number_input(
            "Number of Occurrences",
            min_value=1,
            max_value=365,
            value=1,
            disabled=(recurrence == "None")
        )

        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Create Schedule")

        if submitted:
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
            series_id = generate_id()

            rows = []
            for i in range(occurrences):
                if recurrence == "Daily":
                    delta = timedelta(days=i)
                elif recurrence == "Weekly":
                    delta = timedelta(weeks=i)
                elif recurrence == "Monthly":
                    delta = timedelta(days=30 * i)
                else:
                    delta = timedelta(days=0)

                rows.append({
                    "id": generate_id(),
                    "series_id": series_id,
                    "title": title,
                    "owner": owner,
                    "start": start_dt + delta,
                    "end": end_dt + delta,
                    "priority": priority,
                    "status": status,
                    "recurrence": recurrence,
                    "notes": notes
                })

            st.session_state.events = pd.concat(
                [st.session_state.events, pd.DataFrame(rows)],
                ignore_index=True
            )

            st.success(f"{len(rows)} event(s) scheduled successfully")

# --------------------
# Event List
# --------------------

elif view == "Event List":
    st.title("Scheduled Events")
    st.caption("Enterprise-wide event registry")

    if st.session_state.events.empty:
        st.info("No events scheduled")
    else:
        df = st.session_state.events.sort_values("start")

        filters = st.columns(4)
        owner_filter = filters[0].selectbox("Owner", ["All"] + sorted(df.owner.unique().tolist()))
        priority_filter = filters[1].selectbox("Priority", ["All"] + sorted(df.priority.unique().tolist()))
        status_filter = filters[2].selectbox("Status", ["All"] + sorted(df.status.unique().tolist()))
        recurrence_filter = filters[3].selectbox("Recurrence", ["All"] + sorted(df.recurrence.unique().tolist()))

        if owner_filter != "All":
            df = df[df.owner == owner_filter]
        if priority_filter != "All":
            df = df[df.priority == priority_filter]
        if status_filter != "All":
            df = df[df.status == status_filter]
        if recurrence_filter != "All":
            df = df[df.recurrence == recurrence_filter]

        st.dataframe(df, use_container_width=True, height=420)

# --------------------
# Calendar View
# --------------------

elif view == "Calendar View":
    st.title("Daily Calendar")
    st.caption("Operational visibility by date")

    if st.session_state.events.empty:
        st.info("No events to display")
    else:
        df = st.session_state.events.copy()
        df["date"] = df.start.dt.date

        selected_date = st.date_input("Select Date", date.today())
        daily = df[df.date == selected_date]

        if daily.empty:
            st.info("No scheduled events")
        else:
            for _, row in daily.iterrows():
                with st.container():
                    st.markdown(
                        f"""
                        <div style="border-left: 6px solid #3b82f6; padding: 1rem; margin-bottom: 1rem; background-color: #f8fafc; border-radius: 8px;">
                        <strong>{row['title']}</strong><br>
                        {row['start'].strftime('%H:%M')} – {row['end'].strftime('%H:%M')}<br>
                        Owner: {row['owner']}<br>
                        Priority: {row['priority']} | Recurrence: {row['recurrence']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# --------------------
# Admin Dashboard
# --------------------

elif view == "Admin Dashboard":
    st.title("Admin Dashboard")
    st.caption("Governance, metrics, and export")

    if st.session_state.events.empty:
        st.info("No data available")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events", len(st.session_state.events))
        col2.metric("Recurring Series", st.session_state.events.series_id.nunique())
        col3.metric("Critical Priority", len(st.session_state.events[st.session_state.events.priority == "Critical"]))

        csv = st.session_state.events.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Schedule (CSV)",
            data=csv,
            file_name="enterprise_schedule.csv",
            mime="text/csv"
        )
