from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired
from datetime import date, timedelta

class WeatherForm(FlaskForm):
    location = StringField("Location", validators=[DataRequired()])
    start_date = DateField("Start Date", default=date.today())
    end_date = DateField("End Date", default=date.today() + timedelta(days=4))
    submit = SubmitField("Get Weather")