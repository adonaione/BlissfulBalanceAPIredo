# Import required modules
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from . import db # This line is specific to Flask and may not be relevant to the question
from .models import User # This line is specific to Flask and may not be relevant to the question
from datetime import datetime, timezone


# Create an instance of HTTPBasicAuth for basic authentication
basic_auth = HTTPBasicAuth()

# Create an instance of HTTPTokenAuth for token-based authentication
token_auth = HTTPTokenAuth()


# Define a function that verifies the username and password using a SQL query
@basic_auth.verify_password
def verify(username, password):
    user = db.session.execute(db.select(User).where(User.username==username)).scalar_one_or_none()
    if user is not None and user.check_password(password):
        return user
    return None

# Handle any errors that occur during basic authentication
@basic_auth.error_handler
def handle_error(status_code):
    return {'error': 'Incorrect username and/or password. Please try again'}, status_code

# Define a function that verifies the token using a SQL query
@token_auth.verify_token
def verify(token):
    user = db.session.execute(db.select(User).where(User.token==token)).scalar_one_or_none()
    if user is not None and user.token_expiration > datetime.now(timezone.utc):
        return user
    return None

# Handle any errors that occur during token-based authentication
@token_auth.error_handler
def handle_error(status_code):
    return {'error': 'Incorrect token. Please try again'}, status_code
