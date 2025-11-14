from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from decouple import config
from django.conf import settings
@shared_task(name='send_email_verification')
def send_email_verification(subject, message, to_email):
    try:
        email = Mail(
            from_email=settings.EMAIL_HOST_USER, 
            to_emails=to_email,
            subject=subject,
            html_content=message,)
        print(email)
        sg = SendGridAPIClient(settings.SEND_GRID_API_KEY)
        response = sg.send(email)
        print(response)
        # Optional: log response status for debugging
        print(f"SendGrid Response: {response.status_code}")
        return response.status_code == 202  # 202 is success for SendGrid
    except Exception as e:
        if hasattr(e, 'body'):
            print("SendGrid error body:", e.body)
        raise    
    
@shared_task(name='send_rest_password_email')
def send_rest_password_email(subject, message, to_email):
    try:
        email = Mail(
            from_email=settings.EMAIL_HOST_USER, 
            to_emails=to_email,
            subject=subject,
            html_content=message,)
        print(email)
        sg = SendGridAPIClient(settings.SEND_GRID_API_KEY)
        response = sg.send(email)
        print(response)
        print(f"SendGrid Response: {response.status_code}")
        return response.status_code == 202  # 202 is success for SendGrid
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

