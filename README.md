# My Blog

This is a simple blog application built with Flask. The project is now organised as a package following the application factory pattern.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure the following environment variables are set:
   - `GMAIL_SMTP_ADDRESS`
   - `GMAIL_SMTP_EMAIL`
   - `GMAIL_SMTP_PASSWORD`
   - `FLASK_KEY`
   - Optional: `DB_URL` for a custom database URL
3. Start the application:
   ```bash
   python wsgi.py
   ```

The Dockerfile can also be used to run the app in a container.
