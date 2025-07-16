from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from mongoengine import connect
from models import User, Event, Registrations, Feedback
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

connect(db="test", host="localhost", port=27017)

SENDGRID_API_KEY = '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'
FROM_EMAIL = 'eventmanagementoffice.pucit@gmail.com'  # verified sender

def send_email(to_email, subject, html_content):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print(f"Email sent to {to_email} with subject: {subject}")
    except Exception as e:
        print(f"Error sending email to {to_email}:", e)


def send_event_reminders():
    print("Checking for events to send reminders...")

    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"Tomorrow's date: {tomorrow}")

    events = Event.objects(date=tomorrow)
    print(f"Events found for tomorrow: {events.count()}")

    for event in events:
        print(f"\nEvent: {event.title} (ID: {event.id})")
        registrations = Registrations.objects(event_id=str(event.id))
        print(f"Registrations found: {registrations.count()}")

        for reg in registrations:
            user = User.objects(id=reg.user_id).first()
            if user:
                print(f"Sending reminder to user: {user.name}, Email: {user.email}")
                html = f"""
                <p>Dear {user.name},</p>
                <p>This is a reminder that you are registered for the following event tomorrow:</p>
                <p><strong>{event.title}</strong><br>
                Date: {event.date.strftime('%A, %B %d, %Y')}<br>
                Time: {event.time}<br>
                Location: {event.location}</p>
                <p>We look forward to seeing you there!</p>
                <p><strong>Event Management Society - PUCIT</strong></p>
                """
                send_email(user.email, f"Reminder: {event.title} is Tomorrow", html)

def send_feedback_requests():
    print("Checking for feedback requests...")
    yesterday = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')

    events = Event.objects(date=yesterday)

    for event in events:
        registrations = Registrations.objects(event_id=str(event.id))
        for reg in registrations:
            user = User.objects(id=reg.user_id).first()
            if user:
                feedback = Feedback.objects(user_id=str(user.id), event_id=str(event.id)).first()
                if not feedback:
                    html = f"""
                    <p>Dear {user.name},</p>
                    <p>Thank you for attending <strong>{event.title}</strong>.</p>
                    <p>We would love to hear your feedback to help us improve.</p>
                    <p><a href="http://localhost:5000/feedback/{event.id}">Click here to provide your feedback</a></p>
                    <p>Thank you!<br><strong>Event Management Society - PUCIT</strong></p>
                    """
                    send_email(user.email, f"We value your feedback on {event.title}", html)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_event_reminders, 'interval', hours=24)
    scheduler.add_job(send_feedback_requests, 'interval', hours=24)
    scheduler.start()
    print("Scheduler started. Running reminder tasks every 24 hours.")


