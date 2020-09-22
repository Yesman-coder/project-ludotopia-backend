from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(25))
    ludos = db.Column(db.Integer())
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    status = db.Column(db.Boolean(), unique=False, nullable=False)

    #aca va el relationship con bet

    def __init__(self, email, name, last_name, phone, ludos, username, password, status):
        self.email = email
        self.name = name
        self.last_name = last_name
        self.phone = phone
        self.ludos = ludos
        self.username = username
        self.password = password
        self.status = status
    
    @classmethod
    def register(cls, email, name, last_name, phone, ludos, username, password, status):
        new_user = cls(
            email, 
            name.lower(), 
            last_name.lower(), 
            phone, 
            ludos, 
            username, 
            password, 
            status
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