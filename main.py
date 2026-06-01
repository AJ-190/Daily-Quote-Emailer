import smtplib
import time
import os
from email.mime.text import MIMEText
import random
from dotenv import load_dotenv
load_dotenv()

class Email:
    def __init__(self, to_email):
        self.my_email = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")
        self.from_name = "Addy's Explorer"
        self.to_email = to_email

    def get_random_quote(self):
        quotes = []

        with open(os.path.join(os.path.dirname(__file__), "Motivational_Quotes_Collection.txt"), "r", encoding="utf-8") as f:
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

            if line.startswith('"') and line.endswith('"'):
                current_quote = line.strip('"').strip()

            elif line.startswith("—"):
                current_author = line.replace("—", "").strip()

        if current_quote and current_author:
            quotes.append({"quote": current_quote, "author": current_author})

        return random.choice(quotes)
                
    def message_preparation(self):
        subject = "Grow Your Inner World"
        quote_author = self.get_random_quote()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f7fb; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; padding:20px; border-radius:10px;">
                <h2 style="color:#2b5cbf;">Daily Motivation</h2>
                <p style="font-size:18px;">{quote_author['quote']} ~{quote_author['author']}</p>
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
        for attempt in range(5):
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", port=465) as conn:
                    conn.login(self.my_email, self.password)
                    conn.sendmail(
                        from_addr=self.my_email,
                        to_addrs=self.to_email,
                        msg=msg.as_string()
                    )
                print(f"Email sent to {self.to_email} successfully ✅")
                break
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed for {self.to_email}: {e}")
                time.sleep(10)


if __name__ == "__main__":
    emails = os.getenv("EMAIL_USERS", "")
    
    recipients = [line.strip() for line in emails.split(",") if line.strip()]

    for recipient in recipients:
        email = Email(recipient)
        email.send_email()