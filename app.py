import os
import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import database module
import db
# Import backend agents / chatbot functions
import chatbot
import leave_agent

# Ensure environment variables are loaded
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Attendance AI Agent Dashboard",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS injection
st.markdown("""
<style>
/* Font overrides */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Gradient Title card */
.hero-gradient {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    border-radius: 16px;
    padding: 2.5rem;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.hero-title {
    font-size: 2.75rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(to right, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-tagline {
    font-size: 1.1rem;
    color: #cbd5e1;
    margin-top: 0.5rem;
    font-weight: 300;
}

/* Metric Container hover effects */
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border-color: rgba(96, 165, 250, 0.4);
}

/* Clean sidebar styling */
.sidebar-profile {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
}

/* Text area styling for letters */
textarea {
    font-family: 'Courier New', Courier, monospace !important;
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
    border: 1px solid #334155 !important;
}

/* Table styling override */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


# --- Helper Database Queries ---

def get_today_stats():
    """Calculates attendance stats for the current calendar date."""
    today = datetime.date.today()
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Total students
        cursor.execute("SELECT COUNT(*) AS total FROM userdetails")
        total_students = cursor.fetchone()['total']
        
        # 2. Today's attendance records
        cursor.execute("""
            SELECT userid, checkin 
            FROM userattendance 
            WHERE attendancedate = %s
        """, (today,))
        attendance_rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error querying database for today's statistics: {e}")
        return 0, 0, 0, 0

    # Process metrics
    present_user_ids = set()
    late_count = 0
    
    # Load LATE_AFTER rule
    late_after_str = db.get_setting("LATE_AFTER", "09:45")
    try:
        late_hour, late_minute = map(int, late_after_str.split(':'))
        late_time = datetime.time(late_hour, late_minute)
    except Exception:
        late_time = datetime.time(9, 45)
        
    for row in attendance_rows:
        checkin_val = row['checkin']
        if checkin_val is not None:
            present_user_ids.add(row['userid'])
            # Compare datetime.time
            if isinstance(checkin_val, datetime.datetime):
                if checkin_val.time() > late_time:
                    late_count += 1
            elif isinstance(checkin_val, str):
                try:
                    time_part = datetime.datetime.strptime(checkin_val.split()[1], "%H:%M:%S").time()
                    if time_part > late_time:
                        late_count += 1
                except:
                    pass
                    
    present_count = len(present_user_ids)
    absent_count = total_students - present_count
    
    return total_students, present_count, absent_count, late_count


def get_last_7_days_stats():
    """Queries and returns Present vs Absent counts for the last 7 calendar days."""
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Total registered students
        cursor.execute("SELECT COUNT(*) AS total FROM userdetails")
        total_students = cursor.fetchone()['total']
        
        # Get count of present students per day
        format_strings = ','.join(['%s'] * len(dates))
        cursor.execute(f"""
            SELECT attendancedate, COUNT(DISTINCT userid) AS present_count
            FROM userattendance
            WHERE attendancedate IN ({format_strings}) AND checkin IS NOT NULL
            GROUP BY attendancedate
        """, tuple(dates))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error querying database for historical chart: {e}")
        return pd.DataFrame()

    # Map results
    db_counts = {}
    for r in rows:
        ad = r['attendancedate']
        if isinstance(ad, datetime.date):
            d_key = ad
        else:
            d_key = datetime.datetime.strptime(str(ad).split()[0], "%Y-%m-%d").date()
        db_counts[d_key] = r['present_count']
        
    chart_data = []
    for d in dates:
        present = db_counts.get(d, 0)
        present = min(present, total_students)  # Sanity check
        absent = total_students - present
        chart_data.append({
            "Date": d.strftime("%b %d"),
            "Present": present,
            "Absent": absent
        })
        
    df = pd.DataFrame(chart_data)
    df.set_index("Date", inplace=True)
    return df


# --- Sidebar: Setup & Student Context Selection ---

st.sidebar.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=64)
st.sidebar.title("System Control")

# Load registered students for dropdown list
try:
    userdetails_df = db.get_userdetails_df()
except Exception as e:
    st.sidebar.error(f"Failed to fetch students: {e}")
    userdetails_df = pd.DataFrame(columns=["id", "name", "email", "gender", "contact", "country"])

# Prepare Student options
student_options = ["None (General Context)"]
student_map = {}
for _, row in userdetails_df.iterrows():
    option_label = f"{row['name']} (ID: {row['id']})"
    student_options.append(option_label)
    student_map[option_label] = row

selected_option = st.sidebar.selectbox(
    "Select Student Context for Chatbot",
    options=student_options,
    help="Selecting a student automatically forwards their ID as context to chatbot queries."
)

active_student_id = None
if selected_option != "None (General Context)":
    student_data = student_map[selected_option]
    active_student_id = int(student_data['id'])
    
    # Display elegant profile sidebar card
    st.sidebar.markdown("### Active Student Context")
    st.sidebar.markdown(f"""
    <div class="sidebar-profile">
        <b>Name:</b> {student_data['name']}<br/>
        <b>ID:</b> {student_data['id']}<br/>
        <b>Email:</b> {student_data['email']}<br/>
        <b>Gender:</b> {student_data['gender']}<br/>
        <b>Contact:</b> {student_data['contact']}<br/>
        <b>Location:</b> {student_data['state']}, {student_data['country']}
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.info("No active student context. Chatbot will run in global search mode.")


# --- Main Dashboard ---

# Hero Title block
st.markdown(f"""
<div class="hero-gradient">
    <h1 class="hero-title">Attendance Analysis & Automation Agent</h1>
    <div class="hero-tagline">AI-powered tracking, predictive compliance alerts, and autonomous communications</div>
</div>
""", unsafe_allow_html=True)

# 1. Today's attendance summary (st.metric row)
total_stu, present, absent, late = get_today_stats()

st.subheader("📅 Today's Attendance Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Students Registered", value=total_stu)
with col2:
    st.metric(label="Present Today", value=present, delta=f"{present/total_stu*100:.1f}%" if total_stu else None)
with col3:
    st.metric(label="Absent Today", value=absent, delta=f"-{absent/total_stu*100:.1f}%" if total_stu else None, delta_color="inverse")
with col4:
    st.metric(label="Late Check-ins", value=late, delta="Requires warning" if late else None, delta_color="off")

st.markdown("---")

# 2. Historical patterns and low attendance split-view
col_chart, col_low = st.columns([3, 2])

with col_chart:
    st.subheader("📊 7-Day Attendance Trend")
    chart_df = get_last_7_days_stats()
    if not chart_df.empty:
        st.bar_chart(chart_df, color=["#3b82f6", "#ef4444"])
    else:
        st.info("No attendance records found to plot.")

with col_low:
    st.subheader("⚠️ Low Attendance Warnings")
    min_pct_str = db.get_setting("MIN_ATTENDANCE_PERCENT", "75")
    st.markdown(f"Students with overall attendance below **{min_pct_str}%**:")
    
    try:
        low_attendance_students = chatbot.get_low_attendance_students()
        if low_attendance_students:
            low_df = pd.DataFrame(low_attendance_students)
            low_df['attendance_pct'] = low_df['attendance_pct'].map(lambda x: f"{x:.1f}%")
            low_df.rename(columns={
                "id": "Student ID",
                "name": "Name",
                "email": "Email",
                "attendance_pct": "Rate"
            }, inplace=True)
            st.dataframe(low_df, use_container_width=True, hide_index=True)
        else:
            st.success("All students are compliant with attendance requirements.")
    except Exception as e:
        st.error(f"Could not load low attendance list: {e}")

st.markdown("---")

# 4. Pending Leave Requests Section
st.subheader("📥 Pending Leave Requests")
try:
    pending_leaves = leave_agent.get_pending_leaves()
    if pending_leaves:
        for idx, req in enumerate(pending_leaves):
            req_id = req['id']
            with st.container(border=True):
                c_info, c_action = st.columns([3, 1])
                with c_info:
                    st.markdown(f"##### Request ID: **{req_id}** — **{req['student_name']}** (ID: {req['student_id']})")
                    st.write(f"**Submitted at:** {req['created_at']} | **Email:** {req['student_email']}")
                    st.markdown(f"**Stated Reason:** *\"{req['reason_raw']}\"*")
                    st.text_area(
                        "AI-Generated Leave Letter",
                        value=req['letter_generated'],
                        height=160,
                        disabled=True,
                        key=f"letter_{req_id}_{idx}"
                    )
                with c_action:
                    st.write("") # Adjust height spacing
                    st.write("")
                    st.write("")
                    if st.button("Approve Request", key=f"approve_{req_id}_{idx}", type="primary", use_container_width=True):
                        leave_agent.approve_leave(req_id)
                        st.toast(f"Leave request #{req_id} APPROVED!", icon="✅")
                        st.rerun()
                    st.write("")
                    if st.button("Reject Request", key=f"reject_{req_id}_{idx}", use_container_width=True):
                        leave_agent.reject_leave(req_id)
                        st.toast(f"Leave request #{req_id} REJECTED!", icon="❌")
                        st.rerun()
    else:
        st.info("No pending leave requests at this time.")
except Exception as e:
    st.error(f"Could not fetch pending leave requests: {e}")

st.markdown("---")

# 5. Interactive Chatbot Section
st.subheader("💬 AI Attendance Assistant Chat")
if active_student_id:
    st.markdown(f"Currently chatting with **{selected_option}** set as context.")
else:
    st.markdown("Currently chatting in **General Context**. (Select a student in the sidebar to ask student-specific questions)")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Input
if user_prompt := st.chat_input("Ask a question (e.g., 'Who is absent today?', 'What is my attendance percentage?')"):
    # Append user question
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
        
    # Generate bot answer
    with st.spinner("Analyzing attendance database..."):
        try:
            bot_reply = chatbot.answer_question(user_prompt, active_student_id)
        except Exception as e:
            bot_reply = f"Sorry, I ran into an error while processing your request: {e}"
            
    # Append bot reply
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
