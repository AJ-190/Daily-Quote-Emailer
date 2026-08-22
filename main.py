import smtplib
import time
import os
import sys
import html
import logging
import random
from email.mime.text import MIMEText
from dotenv import load_dotenv
from smtplib import SMTPAuthenticationError
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    # Class variable to store quotes (loaded once for performance)
    _quotes = None

    def __init__(self, to_email: str, my_email: str, password: str):
        self.my_email = my_email
        self.password = password
        self.from_name = "Addy's Explorer"
        self.to_email = to_email
        
        # Load quotes once on first instantiation
        if Email._quotes is None:
            Email._quotes = self._load_quotes()

    @classmethod
    def _load_quotes(cls):
        """Load and parse quotes from file once."""
        quotes = []

        try:
            with open(QUOTE_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning("Could not read quotes file %s: %s", QUOTE_FILE, e)
            return [DEFAULT_QUOTE]

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
            return [DEFAULT_QUOTE]

        return quotes

    def get_random_quote(self):
        """Get a random quote from cached quotes."""
        if not Email._quotes:
            return DEFAULT_QUOTE
        return random.choice(Email._quotes)

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
        """Send email with exponential backoff retry logic."""
        msg = self.message_preparation()
        max_attempts = 5
        base_delay = 2  # seconds
        
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
                    sleep_time = base_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info("Retrying in %s seconds...", sleep_time)
                    time.sleep(sleep_time)
                else:
                    logger.exception("All attempts failed for %s", self.to_email)
                    return False


def parse_recipients(env_value: str):
    """Parse recipients from environment variable supporting multiple separators."""
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


def send_emails_to_recipients(recipients, my_email, password, max_workers=5):
    """Send emails to multiple recipients concurrently."""
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_email = {
            executor.submit(Email(recipient, my_email, password).send_email): recipient
            for recipient in recipients
        }

        # Process completed tasks
        for future in as_completed(future_to_email):
            recipient = future_to_email[future]
            try:
                success = future.result()
                results[recipient] = success
            except Exception as e:
                logger.error("Unexpected error processing %s: %s", recipient, e)
                results[recipient] = False

    return results


def main():
    my_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    emails_env = os.getenv("EMAIL_USERS")

    missing = []
    if not my_email:
        missing.append("EMAIL_USER")
    if not password:
        missing.append("EMAIL_PASS")
    if not emails_env:
        missing.append("EMAIL_USERS")

    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        logger.error("Set the missing variables as GitHub repository Secrets (Settings → Secrets → Actions)")
        sys.exit(1)

    recipients = parse_recipients(emails_env)
    if not recipients:
        logger.error("No recipients found in EMAIL_USERS. Please set EMAIL_USERS (comma/semicolon/newline separated)")
        sys.exit(1)

    logger.info("Found %d recipient(s). Beginning send...", len(recipients))

    results = send_emails_to_recipients(recipients, my_email, password, max_workers=5)
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    logger.info("Email send summary: %d successful, %d failed", successful, failed)

    if failed > 0:
        logger.error("One or more emails failed to send. See logs above for details.")
        sys.exit(2)

    logger.info("All emails sent successfully.")


if __name__ == "__main__":
    main()
