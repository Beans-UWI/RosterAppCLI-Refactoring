from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    active_token = db.Column(db.String, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": "role"
    }   
    
    def __init__(self, username, password, role="user"):
        self.username = username
        self.role = role
        self.set_password(password)

    def get_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)


