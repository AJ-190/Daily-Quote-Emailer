import random
import os
import smtplib
import time

class EmailSender:
    
    def __init__(self, to_email):
        self.my_email = "adysamuel68@gmail.com"
        self.password = "eepg fjyg lcmg ejvt"
        self.from_name = "CoreNerve.AI"
        self.to_email = to_email
        
    def get_random_quote(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        quotes_path = os.path.join(script_dir, "quotes.txt")
        with open(quotes_path, "r") as file:
            quotes = file.readlines()
        return random.choice(quotes).strip()
      
    def send_email(self):
         subject = "Groow Your Inner world"
         quote = self.get_random_quote()

         html_body = f"""
         <html>
         <head>
             <style>
                 body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fb; margin: 0; }}
                 .container {{ max-width: 700px; margin: 35px auto; padding: 28px; background: #ffffff; border-radius: 18px; box-shadow: 0 14px 32px rgba(43, 88, 190, 0.18); }}
                 h1 {{ color: #2b5cbf; text-align: center; margin-bottom: 16px; }}
                 p.quote {{ font-size: 1.2rem; line-height: 1.6; color: #3a3f57; padding: 18px; border-left: 4px solid #2b5cbf; background: #eef2fd; border-radius: 8px; }}
                 p.footer {{ margin-top: 22px; color: #6c7589; text-align: center; font-size: 0.95rem; }}
                 .button {{ display: inline-block; margin: 24px auto 0; padding: 12px 26px; color: #fff; background: linear-gradient(135deg, #2b72d1, #5f85dc); border-radius: 10px; text-decoration: none; font-weight: 600; }}
             </style>
         </head>
         <body>
             <div class="container">
                 <h1>Daily Motivation</h1>
                 <p class="quote">{quote}</p>
                 <p class="footer">Sent with by {self.from_name}. Keep shining and keep growing!</p>
                 <div style="text-align: center;"><a class="button" href="https://github.com/">Explore more inspiration</a></div>
             </div>
         </body>
         </html>
         """

         msg = (
             f"From: {self.from_name} <{self.my_email}>\r\n"
             f"To: {self.to_email}\r\n"
             f"Subject: {subject}\r\n"
             "MIME-Version: 1.0\r\n"
             "Content-Type: text/html; charset=UTF-8\r\n"
             "\r\n"
             f"{html_body}"
         )

         for attempt in range(20):
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", port=465, timeout=30) as conn:
                    conn.login(self.my_email, self.password)
                    conn.sendmail(from_addr=self.my_email, to_addrs=self.to_email, msg=msg)
                print(f"Email sent to {self.to_email} successfully ✅")
                break
            except Exception as e:
                print(f"Error: {e}")
        
                time.sleep(10)
                    
                

# Example usage
if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "emails.txt"), "r") as f:
        mails = [line.strip() for line in f]
        
        for emai in mails:
            email = EmailSender(emai)
            email.send_email()