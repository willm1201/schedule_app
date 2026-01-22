# app.py
# Enterprise-grade Scheduling App for Streamlit Cloud

import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import uuid

st.set_page_config(page_title="Enterprise Scheduler", layout="wide")

# --------------------
# Utilities
# --------------------

def generate_id():
    return str(uuid.uuid4())

if "events" not in st.session_state:
    st.session_state.events = pd.DataFrame(columns=[
        "id", "title", "owner", "start", "end", "priority", "status", "notes"
    ])

# --------------------
# Sidebar – Controls
# --------------------

st.sidebar.title("📅 Scheduler Controls")
view = st.sidebar.radio("View", ["Create Event", "Event List", "Calendar View", "Admin"])

# --------------------
# Create Event
# --------------------

if view == "Create Event":
    st.header("Create New Event")

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
        status = st.selectbox("Status", ["Planned", "Confirmed", "Completed", "Cancelled"])
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Create Event")

        if submitted:
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)

            new_event = {
                "id": generate_id(),
                "title": title,
                "owner": owner,
                "start": start_dt,
                "end": end_dt,
                "priority": priority,
                "status": status,
                "notes": notes
            }

            st.session_state.events = pd.concat([
                st.session_state.events,
                pd.DataFrame([new_event])
            ], ignore_index=True)

            st.success("Event created successfully")

# --------------------
# Event List
# --------------------

elif view == "Event List":
    st.header("All Scheduled Events")

    if st.session_state.events.empty:
        st.info("No events scheduled")
    else:
        df = st.session_state.events.copy()
        df = df.sort_values(by="start")
        st.dataframe(df, use_container_width=True)

        st.subheader("Delete Event")
        delete_id = st.selectbox("Select Event ID", df["id"])
        if st.button("Delete"):
            st.session_state.events = df[df["id"] != delete_id]
            st.warning("Event deleted")

# --------------------
# Calendar View
# --------------------

elif view == "Calendar View":
    st.header("Calendar View")

    if st.session_state.events.empty:
        st.info("No events to display")
    else:
        df = st.session_state.events.copy()
        df["date"] = df["start"].dt.date

        selected_date = st.date_input("Select Date", date.today())
        daily = df[df["date"] == selected_date]

        if daily.empty:
            st.info("No events for selected date")
        else:
            for _, row in daily.iterrows():
                with st.expander(f"{row['title']} ({row['start'].strftime('%H:%M')} - {row['end'].strftime('%H:%M')})"):
                    st.write(f"Owner: {row['owner']}")
                    st.write(f"Priority: {row['priority']}")
                    st.write(f"Status: {row['status']}")
                    st.write(row['notes'])

# --------------------
# Admin
# --------------------

elif view == "Admin":
    st.header("Admin / Export")

    if st.session_state.events.empty:
        st.info("No data available")
    else:
        csv = st.session_state.events.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Events as CSV",
            data=csv,
            file_name="events.csv",
            mime="text/csv"
        )

        st.subheader("System Metrics")
        st.metric("Total Events", len(st.session_state.events))
        st.metric("Active Events", len(st.session_state.events[st.session_state.events['status'] != 'Completed']))
