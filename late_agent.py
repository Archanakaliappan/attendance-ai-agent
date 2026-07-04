"""
late_agent.py
AI-Powered Late Attendance Explanation Generator and Manager.
Uses the new google.genai SDK to generate apologetic late explanations.
"""

import os
import mysql.connector
from dotenv import load_dotenv
from google import genai

# Import database module
import db

load_dotenv()

# Configure new Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("[ERROR] GEMINI_API_KEY not found in .env file or environment variables.")
client = genai.Client(api_key=api_key)


def init_late_table():
    """Initializes agent_late_explanations table in MySQL database if it does not exist."""
    print("[INIT] Verifying late explanation tables in database...")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_late_explanations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            reason_raw TEXT NOT NULL,
            letter_generated TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES userdetails(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[INIT] Late explanation tables verified.")


def generate_late_explanation(student_name: str, reason_text: str) -> str:
    """
    Sends a prompt to Gemini using the new google.genai SDK to convert an informal
    reason for lateness into a short, polite, apologetic explanation.
    """
    prompt = f"""
    Write a short, polite, apologetic explanation for being late to class/work.
    Student Name: {student_name}
    Reason for lateness: {reason_text}
    
    Requirements:
    - Keep it under 100 words
    - Address it professionally (e.g. "Dear Sir/Madam" or similar)
    - Make sure the tone is apologetic for being late (NOT a leave request for absence)
    - Write only the explanation body, including a professional closing with the student's name
    - Do not include subject lines or markdown formatting (e.g. no ```)
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
            print(f"[WARN] Model {model_name} failed or not available: {e}")
            continue
            
    print("[ERROR] All Gemini models failed. Using fallback template.")
    return (
        f"Dear Sir/Madam,\n\n"
        f"Please accept my sincere apologies for arriving late today due to the following reason: {reason_text}. "
        f"I will do my best to ensure this does not happen again.\n\n"
        f"Sincerely,\n{student_name}"
    )


def submit_late_explanation(student_id: int, reason_text: str) -> int:
    """
    Retrieves student's name, generates late explanation via Gemini,
    inserts into agent_late_explanations, and returns the new row ID.
    """
    # 1. Fetch student name
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM userdetails WHERE id = %s", (student_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Student with ID {student_id} not found in userdetails table.")
        
    student_name = row[0]
    
    # 2. Generate explanation
    print(f"[INFO] Generating late explanation for {student_name}...")
    explanation = generate_late_explanation(student_name, reason_text)
    
    # 3. Insert into agent_late_explanations
    cursor.execute("""
        INSERT INTO agent_late_explanations (student_id, reason_raw, letter_generated)
        VALUES (%s, %s, %s)
    """, (student_id, reason_text, explanation))
    
    new_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"[SUCCESS] Late explanation submitted for {student_name} (ID: {student_id}). Row ID: {new_id}")
    return new_id


if __name__ == "__main__":
    # Initialize the database table
    init_late_table()
    
    # Run CLI self-test
    test_student_id = 102
    test_reason = "Bus breakdown"
    
    print("\n--- Running CLI Test ---")
    try:
        new_row_id = submit_late_explanation(test_student_id, test_reason)
        
        # Verify the written entry by fetching it back
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.id, u.name AS student_name, r.reason_raw, r.letter_generated, r.created_at
            FROM agent_late_explanations r
            JOIN userdetails u ON r.student_id = u.id
            WHERE r.id = %s
        """, (new_row_id,))
        record = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print("\n================ Generated Late Explanation ================")
        print(f"Record ID:   {record['id']}")
        print(f"Student:     {record['student_name']} (ID: {test_student_id})")
        print(f"Reason Raw:  {record['reason_raw']}")
        print(f"Created At:  {record['created_at']}")
        print("------------------------------------------------------------")
        print(record['letter_generated'])
        print("============================================================")
        
    except Exception as e:
        print(f"[ERROR] CLI Test failed: {e}")
