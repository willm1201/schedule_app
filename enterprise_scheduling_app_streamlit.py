# app.py
# Enterprise Scheduling Platform – AWS & Postgres Ready

import os
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import uuid
import bcrypt
from sqlalchemy import create_engine, text

# --------------------
# Configuration
# --------------------

st.set_page_config(page_title="Enterprise Scheduler", layout="wide")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    st.error("DATABASE_URL environment variable not set")
    st.stop()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# --------------------
# Database Init
# --------------------

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        );
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS events (
            id UUID PRIMARY KEY,
            series_id UUID,
            title TEXT,
            owner TEXT,
            start_ts TIMESTAMP,
            end_ts TIMESTAMP,
            priority TEXT,
            status TEXT,
            recurrence TEXT,
            notes TEXT
        );
    """))

# --------------------
# Auth Utilities
# --------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# --------------------
# Session Init
# --------------------

if "user" not in st.session_state:
    st.session_state.user = None

# --------------------
# Authentication
# --------------------

if st.session_state.user is None:
    st.title("Secure Enterprise Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            with engine.connect() as conn:
                row = conn.execute(text(
                    "SELECT id, username, role, password_hash FROM users WHERE username=:u"
                ), {"u": username}).fetchone()

            if row and verify_password(password, row.password_hash):
                st.session_state.user = {
                    "id": row.id,
                    "username": row.username,
                    "role": row.role
                }
                st.success("Login successful")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        role = st.selectbox("Role", ["User", "Admin"])
        if st.button("Register"):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO users VALUES (:id,:u,:p,:r)"
                    ), {
                        "id": str(uuid.uuid4()),
                        "u": new_user,
                        "p": hash_password(new_pass),
                        "r": role
                    })
                st.success("User registered")
            except Exception:
                st.error("Username already exists")

    st.stop()

# --------------------
# Sidebar
# --------------------

st.sidebar.title("Enterprise Scheduler")
st.sidebar.caption(f"User: {st.session_state.user['username']} ({st.session_state.user['role']})")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.experimental_rerun()

view = st.sidebar.radio("Navigation", [
    "Create Event",
    "My Events",
    "Calendar",
    "Admin Dashboard" if st.session_state.user["role"] == "Admin" else ""
])

# --------------------
# Create Event
# --------------------

if view == "Create Event":
    st.header("Create Event or Recurring Series")

    with st.form("event_form"):
        title = st.text_input("Title")
        col1, col2 = st.columns(2)
        with col1:
            sd = st.date_input("Start Date", date.today())
            stt = st.time_input("Start Time", time(9, 0))
        with col2:
            ed = st.date_input("End Date", date.today())
            ett = st.time_input("End Time", time(10, 0))

        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        recurrence = st.selectbox("Recurrence", ["None", "Daily", "Weekly", "Monthly"])
        count = st.number_input("Occurrences", 1, 365, 1, disabled=(recurrence == "None"))
        notes = st.text_area("Notes")

        submit = st.form_submit_button("Create")

        if submit:
            start_dt = datetime.combine(sd, stt)
            end_dt = datetime.combine(ed, ett)
            series_id = uuid.uuid4()

            rows = []
            for i in range(count):
                if recurrence == "Daily":
                    delta = timedelta(days=i)
                elif recurrence == "Weekly":
                    delta = timedelta(weeks=i)
                elif recurrence == "Monthly":
                    delta = timedelta(days=30*i)
                else:
                    delta = timedelta()

                rows.append({
                    "id": uuid.uuid4(),
                    "series_id": series_id,
                    "title": title,
                    "owner": st.session_state.user['username'],
                    "start_ts": start_dt + delta,
                    "end_ts": end_dt + delta,
                    "priority": priority,
                    "status": "Planned",
                    "recurrence": recurrence,
                    "notes": notes
                })

            with engine.begin() as conn:
                for r in rows:
                    conn.execute(text("""
                        INSERT INTO events VALUES
                        (:id,:sid,:t,:o,:s,:e,:p,:st,:r,:n)
                    """), {
                        "id": r['id'], "sid": r['series_id'], "t": r['title'], "o": r['owner'],
                        "s": r['start_ts'], "e": r['end_ts'], "p": r['priority'],
                        "st": r['status'], "r": r['recurrence'], "n": r['notes']
                    })

            st.success(f"{len(rows)} event(s) created")

# --------------------
# My Events
# --------------------

elif view == "My Events":
    st.header("My Scheduled Events")
    with engine.connect() as conn:
        df = pd.read_sql(text(
            "SELECT * FROM events WHERE owner=:o ORDER BY start_ts"
        ), conn, params={"o": st.session_state.user['username']})

    st.dataframe(df, use_container_width=True)

# --------------------
# Calendar (Full Calendar View)

from streamlit_calendar import calendar

calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    },
    "height": 650,
}

# --------------------

elif view == "Calendar":
    st.header("Enterprise Calendar")
    st.caption("Interactive scheduling calendar")

    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM events", conn)

    calendar_events = []
    for _, r in df.iterrows():
        calendar_events.append({
            "title": f"{r['title']} ({r['priority']})",
            "start": r['start_ts'].isoformat(),
            "end": r['end_ts'].isoformat(),
        })

    calendar(calendar_events, options=calendar_options)

# --------------------
# Admin Dashboard
# --------------------

elif view == "Admin Dashboard" and st.session_state.user['role'] == "Admin":
    st.header("Admin Dashboard")

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM events")).scalar()
        users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()

    c1, c2 = st.columns(2)
    c1.metric("Total Events", total)
    c2.metric("Total Users", users)

    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM events", conn)
    st.dataframe(df, use_container_width=True)
