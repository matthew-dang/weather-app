from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date


db = SQLAlchemy()

class WeatherEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float)
    description = db.Column(db.String(100))
    start_date = db.Column(Date)
    end_date = db.Column(Date)