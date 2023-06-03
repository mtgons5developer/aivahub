import smtplib
import schedule
import time

def send_email():
    # Gmail account details
    gmail_user = 'your_email@gmail.com'
    gmail_password = 'your_password'

    # Recipient email address
    to = 'recipient_email@example.com'

    # Email content
    subject = 'Scheduled Email'
    body = 'This is a scheduled email sent from Python.'

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (gmail_user, ", ".join(to), subject, body)

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)

        # Send the email
        server.sendmail(gmail_user, to, email_text)
        server.close()

        print('Email sent successfully.')

    except Exception as e:
        print('Error sending email:', str(e))

# Schedule the email to be sent at a specific time
schedule.every().day.at('09:00').do(send_email)

# Continuously run the scheduled jobs
while True:
    schedule.run_pending()
    time.sleep(1)
