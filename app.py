from flask import Flask, flash, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from forms import WeatherForm
from weather import get_weather_data, get_coordinates, get_5_day_forecast, get_forecast_from_onecall
from models import db, WeatherEntry
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
import os
import csv
import json
import io

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
    forecast_display = []
    map_url = None

    unit = request.form.get('unit', 'metric') if request.method == 'POST' else 'metric'
    unit_label = "°C" if unit == "metric" else "°F"
    today = date.today()
    max_date = today + timedelta(days=7)

    location = request.args.get('location')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if location and start_date_str and end_date_str:
        form.location.data = location
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        form.start_date.data = start_date
        form.end_date.data = end_date

        lat, lon = get_coordinates(location)
        if lat:
            map_url = f"https://www.google.com/maps/embed/v1/view?key={os.getenv('GOOGLE_MAPS_API_KEY')}&center={lat},{lon}&zoom=10&maptype=roadmap"
            weather_info = get_weather_data(location, unit)
            raw_forecast = get_forecast_from_onecall(lat, lon, unit)
            forecast_raw = raw_forecast
            forecast_display = [
                (datetime.strptime(date_str, "%Y-%m-%d").strftime("%A"), info)
                for date_str, info in raw_forecast[:5]
            ]
            filtered_forecast = filter_forecast_by_range(raw_forecast, start_date, end_date)

    elif form.validate_on_submit():
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
        
        map_url = f"https://www.google.com/maps/embed/v1/view?key={os.getenv('GOOGLE_MAPS_API_KEY')}&center={lat},{lon}&zoom=10&maptype=roadmap"

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
        max_date=max_date,
        map_url=map_url
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

@app.route('/export/json')
def export_json():
    entries = WeatherEntry.query.all()
    data = [{
        "location": e.location,
        "temperature": e.temperature,
        "description": e.description,
        "start_date": str(e.start_date),
        "end_date": str(e.end_date)
    } for e in entries]
    return Response(json.dumps(data, indent=2), mimetype='application/json',
                    headers={"Content-Disposition": "attachment;filename=weather.json"})

@app.route('/export/csv')
def export_csv():
    entries = WeatherEntry.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Location", "Temperature", "Description", "Start Date", "End Date"])
    for e in entries:
        writer.writerow([e.location, e.temperature, e.description, e.start_date, e.end_date])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=weather.csv"})

@app.route('/export/md')
def export_md():
    entries = WeatherEntry.query.all()
    md = "# Weather Data\n\n| Location | Temp | Description | Start Date | End Date |\n"
    md += "|----------|------|-------------|-------------|-----------|\n"
    for e in entries:
        md += f"| {e.location} | {e.temperature} | {e.description} | {e.start_date} | {e.end_date} |\n"
    return Response(md, mimetype='text/markdown',
                    headers={"Content-Disposition": "attachment;filename=weather.md"})

if __name__ == '__main__':
    app.run(debug=True)


