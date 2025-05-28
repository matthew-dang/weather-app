from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class WeatherForm(FlaskForm):
    location = StringField('Enter a location:', validators=[DataRequired()])
    submit = SubmitField('Get Weather')