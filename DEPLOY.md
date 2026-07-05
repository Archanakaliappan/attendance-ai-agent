# Streamlit Cloud Deployment Guide

This guide outlines the steps to deploy the **AI-Powered Attendance Analysis and Automation Agent** to Streamlit Community Cloud ([share.streamlit.io](https://share.streamlit.io)) and configure its database/AI secrets.

---

## 1. Pushing Code to GitHub
To push your latest changes to your GitHub repository, execute the following command sequence in your local shell:

```bash
# Check the status of your files
git status

# Stage all updated files
git add .gitignore db.py chatbot.py leave_agent.py late_agent.py monitor.py app.py

# Commit with a clear description
git commit -m "Configure st.secrets fallback for Streamlit Cloud deployment"

# Push to your repository (main branch)
git push origin main
```

---

## 2. Deploying on share.streamlit.io
1. **Sign in to Streamlit Cloud**: Navigate to [share.streamlit.io](https://share.streamlit.io) and click **Sign in with GitHub**.
2. **Create a New App**: Click the **New app** button (usually located in the top-right corner of the workspace dashboard).
3. **Configure Repository Details**:
   - **Repository**: Select or paste your GitHub repository: `your-username/attendance_agent` (e.g. `Archanakaliappan/attendance-ai-agent`).
   - **Branch**: Set this to `main`.
   - **Main file path**: Set this to `app.py`.
4. **Deploy**: Click the **Deploy!** button.

---

## 3. Configuring Secrets on Streamlit Cloud
Streamlit Cloud uses a `secrets.toml` syntax. Paste the following template into the **Secrets** manager during deployment (found under **Advanced settings** before deploying, or in the app's settings dashboard under **Settings > Secrets** once deployed).

> [!IMPORTANT]
> Replace all placeholder values below with your actual database and API credentials. Do not commit actual credentials to GitHub.

```toml
# MySQL Database Connection Details
DB_HOST = "your-database-hostname-or-ip"
DB_PORT = "3306"
DB_USER = "your_db_username"
DB_PASSWORD = "your_db_password"
DB_NAME = "attendancejframebd"

# Gemini AI API Key
GEMINI_API_KEY = "your-actual-gemini-api-key"

# Attendance Rules Configuration
CUTOFF_TIME = "09:30"
LATE_AFTER = "09:45"
SECOND_REMINDER_DELAY_MINUTES = "30"
MIN_ATTENDANCE_PERCENT = "75"

# Admin Reporting & Email Reminders (yagmail)
GMAIL_USER = "your_username@gmail.com"
GMAIL_APP_PASSWORD = "your-16-char-gmail-app-password"
ADMIN_EMAIL = "your_admin_reporting_email@gmail.com"
```

---

## 4. Updates & Redeployments
- **Automated Redeploys**: Whenever you run `git push origin main`, Streamlit Cloud detects the change on GitHub and automatically pulls and rebuilds the app within a minute.
- **Manual Reboot**: If the application hangs or dependencies fail to update, go to your Streamlit dashboard, click the triple dots next to your app name, and select **Reboot**.

---

## 5. Important Limitation: Background Scheduling (`monitor.py`)
> [!WARNING]
> **Streamlit Cloud does not run persistent background jobs.**
> 
> The background monitor agent (`monitor.py` utilizing `APScheduler`) runs a persistent periodic loop that is designed for local machine servers. In contrast, Streamlit Cloud instances are **request-driven** and **ephemeral**:
> - If no users are viewing the dashboard, Streamlit Cloud puts the app to sleep. When it is asleep, background scheduler threads (such as checking attendance every 5 minutes) **will stop running entirely**.
> - Streamlit Cloud containers spin down and restart periodically, meaning standard memory-based schedulers are unreliable.
>
> ### Recommended Solutions for Production:
> 1. **Keep `monitor.py` Running Locally / on a VM**: Continue running `py -3.12 monitor.py` on a local machine, desktop PC, or a dedicated VPS (e.g. AWS EC2, DigitalOcean) that remains online 24/7. Since `monitor.py` connects to the same remote MySQL database, it will work in tandem with the Streamlit Cloud dashboard.
> 2. **External Cron triggers**: Configure a web cron job (e.g., GitHub Actions schedules, cron-job.org, or Google Cloud Scheduler) that periodically pings an endpoint or runs a lightweight script to trigger the check.
