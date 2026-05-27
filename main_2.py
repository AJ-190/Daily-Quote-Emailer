# import smtplib

# my_email = "adysamuel68@gmail.com"
# password = "vfxj qepe yygj wkmi"
# connection = smtplib.SMTP("smtp.gmail.com")

# #transport layer security, we used to encypt our connection to our emial server, if someon intercerpt our emial and because it exncrypted they won;t be able to have access to the message content
# connection.starttls()
# connection.login(user=my_email, password=password)
# connection.sendmail(from_addr=my_email, to_addrs="adysamuel67@gmail.com", msg="Hey How are you doing")
# connection.close()
# print("Email sent ssuccessfully ✅")


import random
import os
import smtplib
import time
from email.mime.text import MIMEText


class EmailSender:

    def __init__(self, to_email):
        self.my_email = "adysamuel68@gmail.com"
        self.password =   "eepg fjyg lcmg ejvt"
        self.from_name = "Infranex.AI"
        self.to_email = self.clean_email(to_email)



    def get_random_quote(self):
        with open(os.path.join(os.path.dirname(__file__), "quotes.txt"), 'r') as file:
            quotes = file.readlines()
        return random.choice(quotes).strip()

    def build_message(self):
        subject = "Grow Your Inner World"
        quote = self.get_random_quote()

        html_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f7fb; padding:20px;">
            <div style="max-width:600px; margin:auto; background:#fff; padding:20px; border-radius:10px;">
                <h2 style="color:#2b5cbf;">Daily Motivation</h2>
                <p style="font-size:18px;">{quote}</p>
                <p style="color:gray;">— {self.from_name} Keep shining and keep growing</p>
            </div>
        </body>
        </html>
        """

        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.my_email}>"
        msg["To"] = self.to_email

        return msg

    def send_email(self):
        msg = self.build_message()

        for attempt in range(3):  
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as conn:
                    conn.login(self.my_email, self.password)
                    conn.sendmail(self.my_email, self.to_email, msg.as_string())

                print(f"✅ Sent to {self.to_email}")
                break

            except Exception as e:
                print(f"❌ Error sending to {self.to_email}: {e}")
                time.sleep(5)
# MAIN
if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "emails.txt"), "r") as file:
        mails = [mail.strip() for mail in file]
    for email in mails:
        sender = EmailSender(email)
        print(repr(sender.to_email))  # debug clean email
        sender.send_email()