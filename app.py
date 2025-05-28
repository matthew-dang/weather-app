from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from forms import WeatherForm
from weather import get_weather_data, get_coordinates, get_5_day_forecast, get_forecast_from_onecall
from models import db, WeatherEntry
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db.init_app(app)

with app.app_context():
    db.create_all()

def filter_forecast_by_range(forecast_list, start_date, end_date):
    filtered = []
    for date_str, info in forecast_list:
        forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if start_date <= forecast_date <= end_date:
            filtered.append((date_str, info))
    return filtered

@app.route('/', methods=['GET', 'POST'])
def index():
    form = WeatherForm()
    weather_info = None
    filtered_forecast = []
    forecast_raw = []
    unit = request.form.get('unit', 'metric') if request.method == 'POST' else 'metric'
    unit_label = "°C" if unit == "metric" else "°F"
    today = date.today()
    max_date = today + timedelta(days=7)

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

        weather_info = get_weather_data(location, unit)
        raw_forecast = get_forecast_from_onecall(lat, lon, unit)
        forecast_raw = raw_forecast  
        forecast_display = []
        for date_str, info in raw_forecast[:5]:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            forecast_display.append((day_name, info))
        filtered_forecast = filter_forecast_by_range(forecast_raw, start_date, end_date)

        entry = WeatherEntry(
            location=location,
            temperature=weather_info['temp'],
            description=weather_info['description'],
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(entry)
        db.session.commit()

    return render_template(
        "index.html",
        form=form,
        weather=weather_info,
        filtered_forecast=filtered_forecast,
        full_5day_forecast=forecast_display if forecast_display else [],
        unit=unit,
        unit_label=unit_label,
        today=today,
        max_date=max_date
    )

@app.route('/results')
def results():
    entries = WeatherEntry.query.all()
    return render_template('results.html', entries=entries)

@app.route('/update/<int:entry_id>', methods=['GET', 'POST'])
def update_entry(entry_id):
    entry = WeatherEntry.query.get_or_404(entry_id)
    form = WeatherForm(obj=entry)

    if form.validate_on_submit():
        entry.location = form.location.data
        entry.start_date = form.start_date.data
        entry.end_date = form.end_date.data

        lat, lon = get_coordinates(entry.location)
        if lat is None:
            flash("Invalid location.")
            return redirect(url_for('update_entry', entry_id=entry_id))

        weather_info = get_weather_data(entry.location)
        entry.temperature = weather_info["temp"]
        entry.description = weather_info["description"]

        db.session.commit()
        flash("Entry updated successfully!")
        return redirect(url_for('results'))

    return render_template("update.html", form=form, entry=entry)

@app.route('/delete/<int:entry_id>', methods=['GET'])
def delete_entry(entry_id):
    entry = WeatherEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted.")
    return redirect(url_for('results'))

if __name__ == '__main__':
    app.run(debug=True)


