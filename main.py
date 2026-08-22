import smtplib
import time
import os
import html
import logging
from email.mime.text import MIMEText
import random
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Email:
    # Class variable to store quotes (loaded once)
    _quotes = None
    _quotes_file = os.path.join(os.path.dirname(__file__), "Motivational_Quotes_Collection.txt")

    def __init__(self, to_email):
        self.my_email = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")
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
            with open(cls._quotes_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            current_quote = None
            current_author = None

            for line in lines:
                line = line.strip()

                if not line or line.startswith("=") or line.startswith("---"):
                    if current_quote and current_author:
                        quotes.append({"quote": current_quote, "author": current_author})
                    current_quote = None
                    current_author = None
                    continue

                if line.startswith('"') and " — " in line:
                    parts = line.split(" — ", 1)
                    current_quote = parts[0].strip('"').strip()
                    current_author = parts[1].strip()

                elif line.startswith('"') and line.endswith('"'):
                    current_quote = line.strip('"').strip()

                elif line.startswith("—"):
                    current_author = line.replace("—", "").strip()

            if current_quote and current_author:
                quotes.append({"quote": current_quote, "author": current_author})

            if not quotes:
                logger.warning("No quotes found in file. Using fallback quote.")
                quotes = [{"quote": "Believe in yourself!", "author": "Unknown"}]

        except FileNotFoundError:
            logger.error(f"Quotes file not found at {cls._quotes_file}")
            quotes = [{"quote": "Believe in yourself!", "author": "Unknown"}]
        except Exception as e:
            logger.error(f"Error loading quotes: {e}")
            quotes = [{"quote": "Believe in yourself!", "author": "Unknown"}]

        return quotes

    def get_random_quote(self):
        """Get a random quote from cached quotes."""
        if not Email._quotes:
            return {"quote": "Believe in yourself!", "author": "Unknown"}
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

        for attempt in range(max_attempts):
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", port=465) as conn:
                    conn.login(self.my_email, self.password)
                    conn.sendmail(
                        from_addr=self.my_email,
                        to_addrs=self.to_email,
                        msg=msg.as_string()
                    )
                logger.info(f"Email sent to {self.to_email} successfully ✅")
                return True

            except smtplib.SMTPAuthenticationError:
                logger.error(f"❌ Authentication failed for {self.to_email}: Invalid email or password")
                return False
            except smtplib.SMTPException as e:
                logger.warning(f"❌ Attempt {attempt + 1}/{max_attempts} failed for {self.to_email}: {e}")
                if attempt < max_attempts - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}/{max_attempts} for {self.to_email}: {e}")
                if attempt < max_attempts - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)

        logger.error(f"❌ Failed to send email to {self.to_email} after {max_attempts} attempts")
        return False


def send_emails_to_recipients(recipients, max_workers=5):
    """Send emails to multiple recipients concurrently."""
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_email = {
            executor.submit(Email(recipient).send_email): recipient
            for recipient in recipients
        }

        # Process completed tasks
        for future in as_completed(future_to_email):
            recipient = future_to_email[future]
            try:
                success = future.result()
                results[recipient] = success
            except Exception as e:
                logger.error(f"Unexpected error processing {recipient}: {e}")
                results[recipient] = False

    return results


if __name__ == "__main__":
    emails = os.getenv("EMAIL_USERS", "")

    recipients = [line.strip() for line in emails.split(",") if line.strip()]

    if not recipients:
        logger.warning("No recipients found in EMAIL_USERS environment variable")
    else:
        logger.info(f"Sending emails to {len(recipients)} recipient(s)")
        results = send_emails_to_recipients(recipients, max_workers=5)

        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful
        logger.info(f"Email send summary: {successful} successful, {failed} failed")
