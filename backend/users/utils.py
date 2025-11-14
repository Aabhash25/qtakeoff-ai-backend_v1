from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage

def password_validation(password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    elif not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit.")
    elif not any(char.isalpha() for char in password):
        raise ValueError("Password must contain at least one letter.")
    elif all(char not in "!@#$%^&*()-_+=<>?/|{}[]:;'" for char in password):
        raise ValueError("Password must contain at least one special character.")
    elif not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    elif not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter.")
    

def generate_verification_email_token(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token

class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject = data['subject'],
            body = data['body'],
            from_email= 'toshiro.limbu01@gmail.com',
            to=[data['to_email']]
        )
        email.send()