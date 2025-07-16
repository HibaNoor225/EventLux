from mongoengine import Document, StringField, BooleanField,IntField,DateField,ListField
from werkzeug.security import generate_password_hash, check_password_hash

class User(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    rollNo = StringField(required=False, unique=True, sparse=True)  # Admins may not need rollNo
    password_hash = StringField(required=True)
    is_admin = BooleanField(default=False)
    email_verified = BooleanField(default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "rollNo": self.rollNo,
            "is_admin": self.is_admin,
            "email_verified": self.email_verified
        }


class Event(Document):
    title = StringField(required=True, max_length=100)
    description = StringField()
    date = DateField(required=True)
    time = StringField(required=True)
    location = StringField(max_length=255)
    capacity = IntField(required=True)
    spots = IntField(required=True)
    registration_deadline = DateField(required=True)

    category = StringField(choices=["Workshop", "Seminar", "Conference", "Hackathon","Sports","Competitions", "Other"])
    images = ListField(StringField())  # List of image paths

    def to_json(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "date": self.date.strftime('%Y-%m-%d'),
            "time": self.time,
            "location": self.location,
            "capacity": self.capacity,
            "spots": self.spots,
            "registration_deadline": self.registration_deadline.strftime('%Y-%m-%d'),
            "category": self.category,
            "images": self.images
        }
class Registrations(Document):
     user_id= StringField(required=True)
     event_id = StringField(required=True)
     meta = {
         'indexes': [
             {
                 'fields': ['user_id', 'event_id'],
                 'unique': True
             }
         ]
     }

     def to_json(self):
            return {
                "id": str(self.id),
                "user_id": self.user_id,
                "event_id": self.event_id
            }


class Feedback(Document):
    user_id = StringField(required=True)
    event_id = StringField(required=True)
    rating= IntField(required=True)
    comments= StringField(required=True)

    meta = {
        'indexes': [
            {
                'fields': ['user_id', 'event_id'],
                'unique': True
            }
        ]
    }

    def to_json(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "event_id": self.event_id,
            "rating": self.rating,
            "comments": self.comments
        }
