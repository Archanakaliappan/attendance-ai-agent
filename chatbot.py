"""
chatbot.py
AI-Powered Attendance Chatbot Agent.
Uses keyword intent matching to run local SQL queries and the new google.genai SDK
to phrase natural-language responses.
"""

import os
import datetime
from dotenv import load_dotenv
from google import genai

# Import database module
import db

load_dotenv()

# Configure Gemini Client
api_key = db.get_setting("GEMINI_API_KEY")
if not api_key:
    raise ValueError("[ERROR] GEMINI_API_KEY not found in .env file or environment variables.")
client = genai.Client(api_key=api_key)


def get_low_attendance_students():
    """
    Fetches students whose attendance percentage is below the threshold
    defined by MIN_ATTENDANCE_PERCENT in the .env file.
    """
    load_dotenv()
    min_pct_str = db.get_setting("MIN_ATTENDANCE_PERCENT", "75")
    try:
        min_pct = float(min_pct_str)
    except ValueError:
        min_pct = 75.0
        
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Left join ensures even students with no attendance records (0.0% attendance) are counted
    cursor.execute("""
        SELECT u.id, u.name, u.email,
               COALESCE((COUNT(CASE WHEN a.checkin IS NOT NULL THEN 1 END) / COUNT(a.id)) * 100, 0.0) AS attendance_pct
        FROM userdetails u
        LEFT JOIN userattendance a ON u.id = a.userid
        GROUP BY u.id, u.name, u.email
        HAVING attendance_pct < %s
    """, (min_pct,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def ask_gemini_phrasing(question: str, db_result_str: str) -> str:
    """
    Sends the database result and original user question to Gemini to phrase
    a single natural-language sentence as the final answer.
    """
    prompt = f"""
    The user asked: "{question}"
    The database returned the following fact: {db_result_str}
    
    Please phrase a single, natural-language sentence as the final answer based on this fact.
    Requirements:
    - Keep the response short, clear, polite, and direct.
    - Return ONLY the phrased sentence. Do not include any introductory remarks, markdown enclosing codeblocks, or extra text.
    """
    
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[WARN] Gemini model {model_name} failed for phrasing: {e}")
            continue
            
    print("[ERROR] All Gemini models failed for phrasing. Using raw DB result as fallback.")
    return db_result_str


def ask_gemini_general(question: str) -> str:
    """
    Sends a general question to Gemini when no database intent matches.
    """
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=question
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[WARN] Gemini model {model_name} failed for general question: {e}")
            continue
            
    return "I'm sorry, I'm having trouble connecting to my AI brain right now. How can I help you?"


def ask_gemini_for_missing_student_id(intent_name: str) -> str:
    """
    Asks Gemini to phrase a polite request for the missing Student ID.
    """
    prompt = (
        f"The user requested information about '{intent_name}' but did not provide their Student ID. "
        f"Phrase a single, polite sentence asking them to provide their Student ID."
    )
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            continue
            
    return "Please provide your Student ID to retrieve this information."


def answer_question(question: str, student_id: int = None) -> str:
    """
    Matches keywords in the user's question, runs corresponding SQL query,
    and calls Gemini to formulate a single natural-language sentence answer.
    """
    import re
    question_lower = question.lower()
    
    # Extract student_id from question text if not provided as an argument
    if not student_id:
        # Match common patterns like "student 101", "id 101", "of 101", "for 101", "user 101"
        match = re.search(r'\b(?:id|student|user|for|of)\s*:?\s*(\d+)\b', question_lower)
        if match:
            student_id = int(match.group(1))
        else:
            # Fallback: scan for any digit sequence but ignore common thresholds (e.g. 75)
            all_numbers = re.findall(r'\b\d+\b', question)
            for num in all_numbers:
                val = int(num)
                # Ignore numbers likely representing percentages or common rule config values
                if val != 75 and val < 1000:
                    student_id = val
                    break
    
    # 1. Intent: Attendance percentage
    if "attendance" in question_lower and any(w in question_lower for w in ["percent", "percentage", "pct", "rate"]):
        if not student_id:
            return ask_gemini_for_missing_student_id("attendance percentage")
            
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(CASE WHEN checkin IS NOT NULL THEN 1 END) AS present_count,
                   COUNT(*) AS total_count
            FROM userattendance
            WHERE userid = %s
        """, (student_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row or row[1] == 0:
            db_result = f"Student ID {student_id} has no attendance records, indicating 0% attendance."
        else:
            present, total = row[0], row[1]
            pct = (present / total) * 100
            db_result = f"Student ID {student_id} has checked in on {present} out of {total} total days, representing {pct:.1f}% attendance."
            
        return ask_gemini_phrasing(question, db_result)
        
    # 2. Intent: Today absent / absentees
    elif ("absent" in question_lower and "today" in question_lower) or "absentees" in question_lower or "today absent" in question_lower or "who is absent" in question_lower or "absent list" in question_lower:
        today = datetime.date.today()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name FROM userdetails
            WHERE id NOT IN (
                SELECT userid FROM userattendance
                WHERE attendancedate = %s AND checkin IS NOT NULL
            )
        """, (today,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            db_result = f"No students are listed as absent today ({today})."
        else:
            names = [f"{r['name']} (ID: {r['id']})" for r in rows]
            db_result = f"On {today}, the following students are absent: " + ", ".join(names)
            
        return ask_gemini_phrasing(question, db_result)
        
    # 3. Intent: Low attendance
    elif "low attendance" in question_lower or ("low" in question_lower and "attendance" in question_lower) or ("below" in question_lower and "attendance" in question_lower) or ("under" in question_lower and "attendance" in question_lower):
        min_pct_str = db.get_setting("MIN_ATTENDANCE_PERCENT", "75")
        rows = get_low_attendance_students()
        
        if not rows:
            db_result = f"All students are currently meeting the attendance target threshold of {min_pct_str}%."
        else:
            students = [f"{r['name']} (ID: {r['id']}) with {r['attendance_pct']:.1f}%" for r in rows]
            db_result = f"The following students are below the target threshold of {min_pct_str}%: " + ", ".join(students)
            
        return ask_gemini_phrasing(question, db_result)
        
    # 4. Intent: Leaves taken
    elif any(w in question_lower for w in ["leave", "leaves", "time off", "vacation"]):
        if not student_id:
            return ask_gemini_for_missing_student_id("leaves taken")
            
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agent_leave_requests WHERE student_id = %s", (student_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        db_result = f"Student ID {student_id} has submitted {count} leave requests in the database."
        return ask_gemini_phrasing(question, db_result)
        
    # 5. Intent: Late count
    elif any(w in question_lower for w in ["late", "tardy", "delay", "behind time"]):
        if not student_id:
            return ask_gemini_for_missing_student_id("late count")
            
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agent_late_explanations WHERE student_id = %s", (student_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        db_result = f"Student ID {student_id} has logged {count} late arrival explanations in the database."
        return ask_gemini_phrasing(question, db_result)
        
    # Default: General Gemini response
    else:
        return ask_gemini_general(question)


if __name__ == "__main__":
    print("=================== Attendance Chatbot Agent ===================")
    print("Type your questions below. Type 'exit' to quit.")
    
    # Optionally configure a student ID
    student_id_input = input("Enter default Student ID for context (or press Enter to skip): ").strip()
    test_student_id = int(student_id_input) if student_id_input.isdigit() else None
    
    if test_student_id:
        print(f"Context set: Student ID = {test_student_id}")
    else:
        print("No Student ID context set. (You can still run general/absent query intents)")
    print("----------------------------------------------------------------")
    
    while True:
        try:
            q = input("\nAsk: ").strip()
            if not q:
                continue
            if q.lower() == "exit":
                print("Exiting chatbot.")
                break
                
            ans = answer_question(q, test_student_id)
            print(f"Bot: {ans}")
            
        except KeyboardInterrupt:
            print("\nExiting chatbot.")
            break
        except Exception as err:
            print(f"Error: {err}")
