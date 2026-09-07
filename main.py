import smtplib
import time
import os
import sys
import logging
import html
import random
from email.mime.text import MIMEText
from dotenv import load_dotenv
from smtplib import SMTPAuthenticationError

# Load local .env if present (only used for local testing)
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

QUOTE_FILE = os.path.join(os.path.dirname(__file__), "Motivational_Quotes_Collection.txt")

DEFAULT_QUOTE = {"quote": "Keep going — small steps every day add up.", "author": "Daily Quote"}


class Email:
    def __init__(self, to_email: str, my_email: str, password: str):
        self.my_email = my_email
        self.password = password
        self.from_name = "Addy's Explorer"
        self.to_email = to_email

    def get_random_quote(self):
        quotes = []

        try:
            with open(QUOTE_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning("Could not read quotes file %s: %s", QUOTE_FILE, e)
            return DEFAULT_QUOTE

        current_quote = None
        current_author = None

        for line in lines:
            line = line.strip()

            # blank or delimiter lines separate entries
            if not line or line.startswith("=") or line.startswith("---"):
                if current_quote:
                    # allow unknown author
                    quotes.append({
                        "quote": current_quote,
                        "author": current_author or "Unknown",
                    })
                current_quote = None
                current_author = None
                continue

            # full line containing both quote and author
            if line.startswith('"') and " — " in line:
                parts = line.split(" — ", 1)
                current_quote = parts[0].strip('"').strip()
                current_author = parts[1].strip()

            elif line.startswith('"') and line.endswith('"'):
                current_quote = line.strip('"').strip()

            elif line.startswith("—"):
                current_author = line.replace("—", "").strip()

        # append the last entry if present
        if current_quote:
            quotes.append({"quote": current_quote, "author": current_author or "Unknown"})

        if not quotes:
            logger.warning("No quotes parsed from file — falling back to default quote")
            return DEFAULT_QUOTE

        return random.choice(quotes)

    def message_preparation(self):
        subject = "Grow Your Inner World"
        quote_author = self.get_random_quote()

        html_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f7fb; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; padding:20px; border-radius:10px;">
                <h2 style="color:#2b5cbf;">Daily Motivation</h2>
                <p style="font-size:18px;">{html.escape(quote_author['quote'])} ~{html.escape(quote_author['author'])}</p>
                <p style="color:gray;">— {self.from_name} | Keep shining and keep growing</p>
            </div>
        </body>
        </html>
        """
        msg = MIMEText(html_body, 'html')
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.my_email}>"
        msg["To"] = self.to_email
        return msg

    def send_email(self):
        msg = self.message_preparation()
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                # Using SSL connection to Gmail
                with smtplib.SMTP_SSL("smtp.gmail.com", port=465, timeout=30) as conn:
                    conn.login(self.my_email, self.password)
                    conn.sendmail(
                        from_addr=self.my_email,
                        to_addrs=[self.to_email],
                        msg=msg.as_string(),
                    )
                logger.info("Email sent to %s successfully ✅", self.to_email)
                return True

            except SMTPAuthenticationError as e:
                logger.error("Authentication failed when sending to %s: %s", self.to_email, e)
                logger.error(
                    "If you use a Google account, make sure you are using an App Password (recommended) or have allowed SMTP access."
                )
                # Authentication errors are unlikely to succeed on retry without changing credentials
                return False

            except Exception as e:
                logger.warning("Attempt %d failed for %s: %s", attempt, self.to_email, e)
                if attempt < max_attempts:
                    sleep_time = 2 ** attempt
                    logger.info("Retrying in %s seconds...", sleep_time)
                    time.sleep(sleep_time)
                else:
                    logger.exception("All attempts failed for %s", self.to_email)
                    return False


def parse_recipients(env_value: str):
    if not env_value:
        return []
    # support comma, semicolon or newline separators
    parts = []
    for sep in [",", ";", "\n"]:
        if sep in env_value:
            parts = [p.strip() for p in env_value.split(sep) if p.strip()]
            break
    if not parts:
        parts = [env_value.strip()]
    return parts


def main():
    my_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    emails_env = os.getenv("EMAILS")

    missing = []
    if not my_email:
        missing.append("EMAIL_USER")
    if not password:
        missing.append("EMAIL_PASS")
    if not emails_env:
        missing.append("EMAILS")

    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        logger.error("Set the missing variables as GitHub repository Secrets (Settings → Secrets → Actions)")
        sys.exit(1)

    recipients = parse_recipients(emails_env)
    if not recipients:
        logger.error("No recipients found in EMAILS. Please set EMAILS (comma/semicolon/newline separated)")
        sys.exit(1)

    logger.info("Found %d recipient(s). Beginning send...", len(recipients))

    any_failures = False
    for recipient in recipients:
        logger.info("Sending to %s", recipient)
        email = Email(recipient, my_email, password)
        success = email.send_email()
        if not success:
            any_failures = True

    if any_failures:
        logger.error("One or more emails failed to send. See logs above for details.")
        sys.exit(2)

    logger.info("All emails sent successfully.")


if __name__ == "__main__":
    main()
