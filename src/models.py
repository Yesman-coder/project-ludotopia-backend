from flask_sqlalchemy import SQLAlchemy
import json
import os
from base64 import b64encode
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(25))
    ludos = db.Column(db.Integer())
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    salt = db.Column(db.String(16), nullable=False)
    status = db.Column(db.Boolean(), nullable=False)

    #aca va el relationship con bet

    def __init__(self, email, name, last_name, phone, ludos, username, password, status):
        self.email = email
        self.name = name
        self.last_name = last_name
        self.phone = phone
        self.ludos = ludos
        self.username = username
        self.set_password(password)
        self.salt = b64encode(os.urandom(4)).decode("utf-8")
        self.status = status
    
    def set_password (self, password):
        self.password_hash = generate_password_hash(f"{password}{self.salt}")
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, f"{password}{self.salt}")

    @classmethod
    def register(cls, email, name, last_name, phone, username, password):
        new_user = cls(
            email, 
            name.lower(), 
            last_name.lower(), 
            phone, 
            100, 
            username, 
            password, 
            True
        )


    def __repr__(self):
        return '<User %r>' % self.username


    def serialize(self):
        return {
            'email' : self.email,
            'name' : self.name,
            'last_name' : self.last_name,
            'phone' : self.phone,
            'ludos' : self.ludos,
            'username' : self.username,
            'status' : self.status
            # do not serialize the password, its a security breach
        }