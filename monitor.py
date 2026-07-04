"""
monitor.py
Attendance monitoring and reminder agent.
Checks database every 5 minutes using APScheduler.
"""

import os
import datetime
import yagmail
import mysql.connector
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Import db module from the local folder
import db

load_dotenv()

def init_tables():
    """Initializes local tracking tables in MySQL if they do not exist."""
    print("[INIT] Verifying tracking tables in database...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Table for logging absentees
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_absent_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            userid INT NOT NULL,
            absent_date DATE NOT NULL,
            marked_at DATETIME NOT NULL,
            UNIQUE KEY unique_user_date (userid, absent_date)
        )
    """)
    
    # Table to prevent replicate emails
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_notification_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            userid INT NOT NULL, -- 0 represents admin summary
            notification_date DATE NOT NULL,
            reminder_type VARCHAR(20) NOT NULL, -- 'first', 'second', 'admin_summary'
            sent_at DATETIME NOT NULL,
            UNIQUE KEY unique_user_date_type (userid, notification_date, reminder_type)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[INIT] Tracking tables verified.")

def is_empty(val):
    """Helper to detect if a field is null, None, or a pandas null placeholder (NaN/NaT)."""
    if val is None:
        return True
    val_str = str(val).strip()
    if val_str in ('None', 'NaT', 'NaN', '<NA>', ''):
        return True
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except:
        pass
    return False

def send_email(to_email, subject, body):
    """Sends an email using yagmail, falling back to console print if credentials are missing."""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pw = os.getenv("GMAIL_APP_PASSWORD")
    
    # Format and log the email to standard output for visibility
    print(f"\n=================== SENDING EMAIL ===================")
    print(f"To:      {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print(f"=====================================================")
    
    if not gmail_user or not gmail_pw or "your_email" in gmail_user or "your_16_char" in gmail_pw:
        print("[WARN] GMail GMAIL_USER or GMAIL_APP_PASSWORD not configured. Skipping actual SMTP send.")
        return True
        
    try:
        yag = yagmail.SMTP(gmail_user, gmail_pw)
        yag.send(to=to_email, subject=subject, contents=body)
        print(f"[SUCCESS] Email successfully dispatched to {to_email} via GMail SMTP.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email} via yagmail: {e}")
        return False

def run_attendance_check():
    """Runs the primary attendance check, cross-referencing userattendance with userdetails."""
    now = datetime.datetime.now()
    today = now.date()
    today_str = today.strftime("%Y-%m-%d")
    
    print(f"\n[CHECK] --- Starting Attendance Scan: {now.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # Parse Timing Configuration
    cutoff_time_str = os.getenv("CUTOFF_TIME", "09:30")
    late_after_str = os.getenv("LATE_AFTER", "09:45")
    second_reminder_delay = int(os.getenv("SECOND_REMINDER_DELAY_MINUTES", "30"))
    admin_email = os.getenv("ADMIN_EMAIL", "admin@domain.com")
    
    try:
        cutoff_hour, cutoff_min = map(int, cutoff_time_str.split(":"))
        cutoff_datetime = now.replace(hour=cutoff_hour, minute=cutoff_min, second=0, microsecond=0)
    except Exception as e:
        print(f"[ERROR] Invalid CUTOFF_TIME format: {cutoff_time_str}. Defaulting to 09:30. Error: {e}")
        cutoff_datetime = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
    try:
        late_hour, late_min = map(int, late_after_str.split(":"))
        late_datetime = now.replace(hour=late_hour, minute=late_min, second=0, microsecond=0)
    except Exception as e:
        print(f"[ERROR] Invalid LATE_AFTER format: {late_after_str}. Defaulting to 09:45. Error: {e}")
        late_datetime = now.replace(hour=9, minute=45, second=0, microsecond=0)
        
    second_reminder_datetime = cutoff_datetime + datetime.timedelta(minutes=second_reminder_delay)
    
    print(f"[RULES] Cutoff Time:       {cutoff_datetime.strftime('%H:%M')}")
    print(f"[RULES] Second Reminder:   {second_reminder_datetime.strftime('%H:%M')} (cutoff + {second_reminder_delay}m)")
    print(f"[RULES] Late After:        {late_datetime.strftime('%H:%M')}")
    print(f"[RULES] Admin Email:       {admin_email}")
    
    # 1. Fetch data from DB
    try:
        userdetails_df = db.get_userdetails_df()
        attendance_df = db.get_attendance_df()
    except Exception as e:
        print(f"[DATABASE ERROR] Could not retrieve data from DB: {e}")
        return
        
    users = userdetails_df.to_dict('records')
    attendance = attendance_df.to_dict('records')
    
    print(f"[DATA] Registered users found: {len(users)}")
    print(f"[DATA] Total historical attendance rows: {len(attendance)}")
    
    # 2. Find students checked in today
    checked_in_user_ids = set()
    for row in attendance:
        ad = row.get('attendancedate')
        if ad is None:
            continue
        if isinstance(ad, (datetime.date, datetime.datetime)):
            row_date_str = ad.strftime("%Y-%m-%d")
        else:
            row_date_str = str(ad).strip().split()[0]
            
        if row_date_str == today_str:
            if not is_empty(row['checkin']):
                checked_in_user_ids.add(int(row['userid']))
                
    print(f"[DATA] Checked-in students today: {len(checked_in_user_ids)}")
    
    # Identify students who have NOT checked in yet
    absent_users = [u for u in users if int(u['id']) not in checked_in_user_ids]
    print(f"[DATA] Unchecked-in students today: {len(absent_users)}")
    
    if not absent_users:
        print("[INFO] All students checked in. Checking admin summary...")
        # Check if we should mark admin summary as complete if everyone is checked in
        return
        
    # 3. Retrieve notification history for today to avoid duplicates
    first_reminders_sent = set()
    second_reminders_sent = set()
    admin_summary_sent = False
    marked_absent_set = set()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Read sent notifications
    cursor.execute("""
        SELECT userid, reminder_type FROM agent_notification_log 
        WHERE notification_date = %s
    """, (today,))
    for uid, r_type in cursor.fetchall():
        if r_type == 'first':
            first_reminders_sent.add(uid)
        elif r_type == 'second':
            second_reminders_sent.add(uid)
        elif r_type == 'admin_summary':
            admin_summary_sent = True
            
    # Read marked absent logs
    cursor.execute("""
        SELECT userid FROM agent_absent_log
        WHERE absent_date = %s
    """, (today,))
    for (uid,) in cursor.fetchall():
        marked_absent_set.add(uid)
        
    # Helper to insert into notification log
    def log_notification(userid, r_type):
        try:
            cursor.execute("""
                INSERT INTO agent_notification_log (userid, notification_date, reminder_type, sent_at)
                VALUES (%s, %s, %s, %s)
            """, (userid, today, r_type, datetime.datetime.now()))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"[DB ERROR] Log notification write failed: {err}")
            
    # 4. Trigger actions based on schedule triggers
    
    # Trigger 1: Cutoff Time (First Reminder)
    if now >= cutoff_datetime:
        print(f"[TRIGGER] Time {now.strftime('%H:%M')} is past cutoff {cutoff_datetime.strftime('%H:%M')}")
        for user in absent_users:
            uid = int(user['id'])
            if uid not in first_reminders_sent:
                subject = f"[Reminder] Class Attendance Check-in Required — {today_str}"
                body = (
                    f"Hi {user['name']},\n\n"
                    f"This is a reminder that you have not checked in for attendance today ({today_str}) "
                    f"as of the cutoff time ({cutoff_time_str}).\n\n"
                    f"Please check in immediately. If you are absent today, please submit "
                    f"a leave request as soon as possible.\n\n"
                    f"Regards,\n"
                    f"Attendance Monitor Bot"
                )
                if send_email(user['email'], subject, body):
                    log_notification(uid, 'first')
                    first_reminders_sent.add(uid)
                    
    # Trigger 2: Cutoff Time + Delay (Second Reminder)
    if now >= second_reminder_datetime:
        print(f"[TRIGGER] Time {now.strftime('%H:%M')} is past second reminder cutoff {second_reminder_datetime.strftime('%H:%M')}")
        for user in absent_users:
            uid = int(user['id'])
            if uid not in second_reminders_sent:
                subject = f"[URGENT Reminder] Second Notice: Attendance Check-in Required — {today_str}"
                body = (
                    f"Hi {user['name']},\n\n"
                    f"This is your second notice that a check-in has not been recorded for you today ({today_str}) "
                    f"by {second_reminder_datetime.strftime('%H:%M')}.\n\n"
                    f"To prevent being marked absent, please verify your check-in status now. "
                    f"If you are key-absent, ensure a leave request is submitted.\n\n"
                    f"Regards,\n"
                    f"Attendance Monitor Bot"
                )
                if send_email(user['email'], subject, body):
                    log_notification(uid, 'second')
                    second_reminders_sent.add(uid)
                    
    # Trigger 3: Late After (Mark Absent and notify admin)
    if now >= late_datetime:
        print(f"[TRIGGER] Time {now.strftime('%H:%M')} is past Late limit {late_datetime.strftime('%H:%M')}")
        
        newly_marked_absent = []
        for user in absent_users:
            uid = int(user['id'])
            if uid not in marked_absent_set:
                # Mark absent in local log
                try:
                    cursor.execute("""
                        INSERT INTO agent_absent_log (userid, absent_date, marked_at)
                        VALUES (%s, %s, %s)
                    """, (uid, today, datetime.datetime.now()))
                    conn.commit()
                    marked_absent_set.add(uid)
                    newly_marked_absent.append(user)
                    print(f"[ABSENT] Student marked absent: {user['name']} (ID: {uid})")
                except mysql.connector.Error as err:
                    print(f"[DB ERROR] Failed to log student {uid} absent: {err}")
                    
        # Send Admin summary email once per day if not sent
        if not admin_summary_sent:
            # Query all marked absent today to make report exhaustive
            cursor.execute("""
                SELECT u.name, u.email FROM agent_absent_log a 
                JOIN userdetails u ON a.userid = u.id
                WHERE a.absent_date = %s
            """, (today,))
            absentees = cursor.fetchall()
            
            subject = f"[Report] Daily Absentee Summary — {today_str}"
            body_lines = [
                f"Hello Admin,\n",
                f"The following students have been marked absent today ({today_str}) ",
                f"because they did not check in by the late time ({late_after_str}):\n"
            ]
            for abs_name, abs_email in absentees:
                body_lines.append(f" - {abs_name} ({abs_email})")
                
            body_lines.append(f"\nTotal Absentees registered: {len(absentees)}")
            body_lines.append(f"\nRegards,\nAttendance Monitoring System")
            
            # Send summary report
            if send_email(admin_email, subject, "\n".join(body_lines)):
                log_notification(0, 'admin_summary')
                admin_summary_sent = True
                
    cursor.close()
    conn.close()
    print("[CHECK] Attendance scan finished.")

if __name__ == "__main__":
    import argparse
    
    print("=========================================================")
    print("      Attendance Monitoring Agent Starting Up            ")
    print("=========================================================")
    
    # 1. Initialize Tables
    init_tables()
    
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="AI-Powered Attendance Analysis and Automation Agent")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check and exit immediately (manual testing)"
    )
    args = parser.parse_args()
    
    if args.once:
        print("\n[INIT] Running single manual check round as requested by --once...")
        run_attendance_check()
        print("\n[INFO] Single check round completed. Exiting.")
    else:
        # 2. Run an immediate check for manual testing
        print("\n[INIT] Running immediate manual check round...")
        run_attendance_check()
        
        # 3. Start APScheduler loop
        print("\n[INIT] Starting APScheduler to check every 5 minutes...")
        scheduler = BlockingScheduler()
        scheduler.add_job(run_attendance_check, 'interval', minutes=5)
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\nShutdown signal received. Exiting monitor agent.")
