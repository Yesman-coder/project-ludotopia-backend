from flask_sqlalchemy import SQLAlchemy
import json
import os
from datetime import datetime, timezone
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
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    salt = db.Column(db.String(16), nullable=False)
    status = db.Column(db.Boolean(), nullable=False)
    bets_sent = db.relationship("Bet", backref="sender", foreign_keys="Bet.sender_id")
    bets_received = db.relationship("Bet", backref="receiver", foreign_keys="Bet.receiver_id")

    #aca va el relationship con bet

    def __init__(self, email, name, last_name, phone, ludos, username, password, status):
        self.email = email
        self.name = name
        self.last_name = last_name
        self.phone = phone
        self.ludos = ludos
        self.username = username
        self.salt = b64encode(os.urandom(4)).decode("utf-8")
        self.set_password(password)
        
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
        return new_user


    def __repr__(self):
        return '<User %r>' % self.username

    

    def serialize(self):
        sent_list = self.bets_sent
        received_list = self.bets_received
        bets_sent_serialize = list(map(lambda bet: bet.serialize(), sent_list))
        bets_received_serialize = list(map(lambda bet: bet.serialize(), received_list))
        # sent = []
        # received = []
        # for bet in sent_list:
        #     receiver = User.query.filter_by(id=bet.receiver_id).first()
        #     info_bet = {}
        #     info_bet["id"] = bet.id
        #     info_bet["receiver"] = receiver.username
        #     info_bet["name"] = bet.name
        #     sent.append(info_bet)
        # for bet in received_list:
        #     sender = User.query.filter_by(id=bet.sender_id).first()
        #     info_bet = {}
        #     info_bet["id"] = bet.id
        #     info_bet["sender"] = sender.username
        #     info_bet["name"] = bet.name
        #     received.append(info_bet)
        return {
            'id' : self.id,
            'email' : self.email,
            'name' : self.name,
            'last_name' : self.last_name,
            'phone' : self.phone,
            'ludos' : self.ludos,
            'username' : self.username,
            'status' : self.status,
            'bets_sent' : bets_sent_serialize,
            'bets_received' : bets_received_serialize
        }

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ludos = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    create_date = db.Column(db.DateTime(timezone=True), nullable=False)
    winner = db.Column(db.String(20))
    state = db.Column(db.String(11), nullable=False)
    status = db.Column(db.Boolean)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, ludos, name, description, due_date, winner, state, status, sender_id, receiver_id):
            self.ludos = ludos
            self.name = name
            self.description = description
            self.due_date = datetime.strptime(due_date, '%Y-%m-%d %I:%M%p')
            self.create_date = datetime.now(timezone.utc)
            self.winner = winner
            self.state = state
            self.status = status
            self.sender_id = sender_id
            self.receiver_id = receiver_id
        
    @classmethod
    def create_bet(cls, ludos, name, description, due_date, sender_id, receiver_id):
        new_bet = cls(
            ludos, 
            name.lower(), 
            description.lower(), 
            due_date,
            "",
            "enviado",
            True,
            sender_id,
            receiver_id
        )
        return new_bet

    def serialize(self):
        return {
            'id' : self.id,
            'ludos' : self.ludos,
            'name' : self.name,
            'description' : self.description,
            'due_date' : self.due_date,
            'create_date' : self.create_date,
            'winner' : self.winner,
            'state' : self.state,
            'status' : self.status,
            'sender_id' : self.sender_id,
            'receiver_id' : self.receiver_id
        }