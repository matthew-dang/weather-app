from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from forms import WeatherForm
from weather import get_weather_data, get_coordinates, get_5_day_forecast
from models import db, WeatherEntry
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = WeatherForm()
    weather_info = None
    forecast = None
    unit = request.form.get('unit', 'metric') if request.method == 'POST' else 'metric'
    unit_label = "°C" if unit == "metric" else "°F"

    if form.validate_on_submit():
        location = form.location.data
        start_date = form.start_date.data
        end_date = form.end_date.data

        if start_date > end_date:
            flash("Start date cannot be after end date.")
            return redirect(url_for("index"))

        lat, lon = get_coordinates(location)
        if lat is None:
            flash("Could not find location.")
            return redirect(url_for("index"))

        weather_info = get_weather_data(location)
        forecast = get_5_day_forecast(lat, lon)

        entry = WeatherEntry(
            location=location,
            temperature=weather_info['temp'],
            description=weather_info['description'],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        db.session.add(entry)
        db.session.commit()

    return render_template("index.html", form=form, weather=weather_info, forecast=forecast, unit=unit, unit_label=unit_label)

@app.route('/results')
def results():
    entries = WeatherEntry.query.all()
    return render_template('results.html', entries=entries)

if __name__ == '__main__':
    app.run(debug=True)