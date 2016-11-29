# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

EMAIL_RECEIPTS = ['ardi.eshghi@gmail.com']

SMTP_HOST = 'email-smtp.eu-west-1.amazonaws.com'
SMTP_USERNAME = "AKIAJXVJFN7S4MN7WOMQ"
SMTP_PASSWORD = "Aq8Q3T/PcbHs55DCf3QJmlfMlvHs0mbRr6Os9EgVAXBH"

def send_email(message = '', to = []):

  # Create a text/plain message
  msg = MIMEText(message)
  to_addr = EMAIL_RECEIPTS + to
  from_email = 'visa-checker@e-ardi.com'

  # you == the recipient's email address
  msg['Subject'] = 'Visa appointment checker notification'
  msg['From'] = from_email

  # Send the message via our own SMTP server, but don't include the
  # envelope header.
  try:
    s = smtplib.SMTP(host=SMTP_HOST, port=587, timeout=10)
    s.starttls()
    s.ehlo()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    s.sendmail(from_email, to_addr, msg.as_string())
    s.quit()
  except Exception as e:
    print(e)

