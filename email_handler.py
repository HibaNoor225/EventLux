from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app

def send_confirmation_email(to_email, event, user_name):
    message = Mail(
        from_email='eventmanagementoffice.pucit@gmail.com',
        to_emails=to_email,
        subject=f"Registration Confirmed: {event.title}",
        html_content=f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #2E86C1;">Registration Confirmed</h2>
            <p>Dear {user_name},</p>
            <p>Thank you for registering for the event:</p>
            <h3 style="color: #1A5276;">{event.title}</h3>
            <p><strong>Date:</strong> {event.date.strftime('%A, %B %d, %Y')}<br>
            <strong>Time:</strong> {event.time}<br>
            <strong>Location:</strong> {event.location}</p>
            <p>We’re excited to have you with us and hope you enjoy the event!</p>
            <br>
            <p>Warm regards,<br>
            <strong>Event Management Society</strong><br>
            PUCIT</p>
        </div>
        """
    )
    try:
        sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
        response = sg.send(message)
        print(response.status_code)
    except Exception as e:
        print("Error sending email:", e)
