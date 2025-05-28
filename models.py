from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class WeatherEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float)
    description = db.Column(db.String(100))
    start_date = db.Column(db.String(10))
    end_date = db.Column(db.String(10))