import requests
import re

API_KEY = "55c6766a3ae6b40761cadb99e5e229a5"

def detect_location_type(location):
    if re.match(r'^-?\d+\.\d+,\s*-?\d+\.\d+$', location):
        return 'coordinates'
    if re.match(r'^\d{5}(?:-\d{4})?$', location):  # Accept 5-digit or ZIP+4
        return 'zip'
    return 'name'

def get_coordinates(location):
    location_type = detect_location_type(location)

    if location_type == 'coordinates':
        lat, lon = map(str.strip, location.split(','))
        print(f"Detected coordinates: lat={lat}, lon={lon}")
        return float(lat), float(lon)

    elif location_type == 'zip':
        geo_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={location},US&appid={API_KEY}"
        response = requests.get(geo_url)
        print(f"ZIP request: {geo_url}")
        if response.status_code == 200:
            data = response.json()
            return data['lat'], data['lon']
        else:
            print("ZIP lookup failed:", response.text)
            return None, None

    else:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={API_KEY}"
        response = requests.get(geo_url)
        print(f"Direct Geo request: {geo_url}")
        data = response.json()
        if response.status_code == 200 and data:
            return data[0]['lat'], data[0]['lon']
        else:
            print("Name lookup failed or returned empty:", response.text)
            return None, None

def get_weather_data(location, units='metric'):
    lat, lon = get_coordinates(location)
    if lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units={units}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'temp': round(data['main']['temp']),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            }
    return None

def get_5_day_forecast(lat, lon, units='metric'):
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units={units}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        daily = {}
        for entry in data['list']:
            day = entry['dt_txt'].split(' ')[0]
            if day not in daily:
                daily[day] = {
                    'temp': round(entry['main']['temp']),
                    'description': entry['weather'][0]['description'],
                    'icon': entry['weather'][0]['icon']
                }
        return list(daily.items())[:5]
    return []