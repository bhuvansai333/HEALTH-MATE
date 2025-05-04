from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    hemoglobin = db.Column(db.Float, nullable=True)
    email = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<User {self.roll_number} - {self.name}>"
