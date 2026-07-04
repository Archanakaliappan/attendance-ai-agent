"""
leave_agent.py
AI-Powered Leave Letter Generator and Request Manager.
Uses Gemini API to convert informal leave reasons into professional letters,
and stores requests in the database for admin approval/rejection.
"""

import os
import mysql.connector
from dotenv import load_dotenv
import google.generativeai as genai

# Import database module
import db

load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("[ERROR] GEMINI_API_KEY not found in .env file or environment variables.")
genai.configure(api_key=api_key)


def init_tables():
    """Initializes agent_leave_requests table in MySQL database if it does not exist."""
    print("[INIT] Verifying leave request tables in database...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Table for leave requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_leave_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            reason_raw TEXT NOT NULL,
            letter_generated TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES userdetails(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[INIT] Leave request tables verified.")


def generate_leave_letter(student_name: str, reason_text: str) -> str:
    """
    Sends a prompt to Gemini to convert an informal reason into a short,
    professional leave letter addressed 'Dear Sir/Madam'.
    """
    prompt = f"""
    Write a short, professional leave letter based on the following details.
    Student Name: {student_name}
    Reason for leave: {reason_text}
    
    Requirements:
    - Address the letter to "Dear Sir/Madam"
    - Keep it short, concise, and professional
    - Write only the letter body, including a professional closing with the student's name
    - Do not include subject lines, placeholders like [Date], or Markdown block formatting (e.g. no ```)
    """
    
    # Try models in order of preference based on available API models
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[WARN] Model {model_name} failed or not available: {e}")
            continue
            
    print("[ERROR] All Gemini models failed. Using fallback template.")
    # Return a fallback simple letter if all API attempts fail
    return (
        f"Dear Sir/Madam,\n\n"
        f"Please accept this letter as formal notification that I, {student_name}, "
        f"am unable to attend class due to the following reason: {reason_text}.\n\n"
        f"Sincerely,\n{student_name}"
    )



def submit_leave_request(student_id: int, reason_text: str) -> str:
    """
    Retrieves student's name from userdetails, generates a professional leave letter via Gemini,
    and inserts a record into agent_leave_requests table with default 'pending' status.
    """
    # 1. Fetch student's name from database
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM userdetails WHERE id = %s", (student_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Student with ID {student_id} not found in userdetails table.")
    
    student_name = row[0]
    
    # 2. Generate the letter using Gemini
    print(f"[INFO] Generating leave letter for {student_name}...")
    letter = generate_leave_letter(student_name, reason_text)
    
    # 3. Store the request in database
    cursor.execute("""
        INSERT INTO agent_leave_requests (student_id, reason_raw, letter_generated, status)
        VALUES (%s, %s, %s, 'pending')
    """, (student_id, reason_text, letter))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[SUCCESS] Leave request submitted for {student_name} (ID: {student_id}).")
    return letter


def approve_leave(request_id: int):
    """Updates the status of a leave request to 'approved'."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE agent_leave_requests
        SET status = 'approved'
        WHERE id = %s
    """, (request_id,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[SUCCESS] Leave request ID {request_id} has been APPROVED.")


def reject_leave(request_id: int):
    """Updates the status of a leave request to 'rejected'."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE agent_leave_requests
        SET status = 'rejected'
        WHERE id = %s
    """, (request_id,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[SUCCESS] Leave request ID {request_id} has been REJECTED.")


def get_pending_leaves():
    """
    Fetches all pending leave requests joined with the student's name and email
    from the userdetails table.
    """
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.id, r.student_id, u.name AS student_name, u.email AS student_email,
               r.reason_raw, r.letter_generated, r.status, r.created_at
        FROM agent_leave_requests r
        JOIN userdetails u ON r.student_id = u.id
        WHERE r.status = 'pending'
        ORDER BY r.created_at DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


if __name__ == "__main__":
    # Initialize the database table
    init_tables()
    
    # Run command-line test for student 103 (Bob Absent)
    test_student_id = 103
    test_reason = "I have fever today"
    
    print("\n--- Running CLI Test ---")
    try:
        generated_letter = submit_leave_request(test_student_id, test_reason)
        print("\nGenerated Leave Letter:")
        print("==================================================")
        print(generated_letter)
        print("==================================================")
        
        # Verify it is in pending leaves
        pending = get_pending_leaves()
        print(f"\nTotal Pending Leave Requests: {len(pending)}")
        for req in pending:
            print(f"- Request ID: {req['id']} | Student: {req['student_name']} (ID: {req['student_id']}) | Status: {req['status']}")
            
    except Exception as e:
        print(f"[ERROR] CLI Test failed: {e}")
