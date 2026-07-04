# Attendance AI Agent — Milestone 1 (Setup + DB Connection)

## What this does right now
Connects to your existing MySQL database (`attendancejframebd`) and confirms
we can read the `userattendance` table and check what's really in `userdetails`.
This does NOT touch your Swing app or write anything to your DB.

## Setup (10 minutes)

1. Install Python 3.10+ if not already installed.
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`:
   ```
   cp .env.example .env
   ```
4. Open `.env` and fill in your real MySQL password (the rest can stay as-is
   if you're running MySQL locally on the default port).
5. Run the self-test:
   ```
   python db.py
   ```

## What you should see
- A list of tables in your database
- The exact column names of `userattendance` (should match: id, userid,
  attendancedate, checkin, checkout, workduration)
- The exact column names of `userdetails` (THIS IS THE IMPORTANT PART —
  copy this output and share it so we lock in the real column names)
- A preview of a few attendance rows

## If you get a connection error
- Most common cause: wrong password in `.env`, or MySQL isn't running.
- Start MySQL (via XAMPP/Workbench/services) and confirm you can log in
  with the same username/password you put in `.env`.

## Next milestone
Once this runs successfully, push this folder to a NEW GitHub repo
(don't mix with your Swing project repo) with:
```
git init
git add .
git commit -m "milestone 1: db connection confirmed"
```
Then tell me it worked and paste the `userdetails` column output —
I'll immediately build Milestone 2 (the attendance monitoring + reminder logic).
