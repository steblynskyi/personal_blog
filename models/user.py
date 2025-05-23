from flask_login import UserMixin
from app import db, login_manager

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
