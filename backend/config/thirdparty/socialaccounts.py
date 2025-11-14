from decouple import config

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_SECRET_KEY'),
            'key': ''
        },
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'FETCH_USERINFO' : True,
        'FIELDS': ['email', 'first_name', 'last_name'],
        "VERIFIED_EMAIL": True,
    }
}
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = config('GOOGLE_SECRET_KEY')
SOCIALACCOUNT_STORE_TOKENS = True

SOCIALACCOUNT_LOGIN_ON_GET = True 
