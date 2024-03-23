#!/usr/bin/env python3
import os
import re
import subprocess
import time
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# Define InfluxDB connection parameters
influx_url = "http://IP:PORT"
influx_org = "org"
influx_token = "ACCESS_TOKEN"
influx_bucket = "BUCKET_NAME"

# Define OpenWeatherMap API token
owm_token = "OMW_ACCESS_TOKEN"

# Call OpenWeatherMap API
response = subprocess.Popen(
    '/usr/bin/curl --location --request GET "https://api.openweathermap.org/data/2.5/weather?q=Berlin&appid=omw_token" --header "Content-Type: application/json"',
    shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')

# Regex pattern to capture temperature, rain, wind, gust, and snow values from the API response
temp_match = re.search('"temp":\s*([\d.]+)', response)
rain_match = re.search('"rain":\s*{\s*"1h":\s*([\d.]+)\s*}', response)
wind_match = re.search('"wind":\s*{\s*"speed":\s*([\d.]+),\s*"deg":\s*[\d.]+,\s*"gust":\s*([\d.]+)', response)
snow_match = re.search('"snow":\s*{\s*"1h":\s*([\d.]+)\s*}', response)

# If temperature data is found in the response
if temp_match:
    temp = temp_match.group(1)

    # Converting temperature from Kelvin to Celsius
    temp_celsius = float(temp) - 273.15
    rounded_temp_celsius = round(temp_celsius, 1)

    # If rain data is available in the response, extract the value
    rain = rain_match.group(1) if rain_match else "0.0"

    # If wind data is available in the response, extract the values for wind speed and gust
    wind_speed_ms = float(wind_match.group(1)) if wind_match else 0.0
    gust_ms = float(wind_match.group(2)) if wind_match else 0.0

    # Convert wind speed and gust from meters per second to kilometers per hour
    wind_speed_kmh = round(wind_speed_ms * 3.6, 2)  # Limit wind speed to two decimal digits
    gust_kmh = round(gust_ms * 3.6, 2)  # Limit gust to two decimal digits

    # If snow data is available in the response, extract the value
    snow = snow_match.group(1) if snow_match else "0.0"

    # Write measurements into the local file
    try:
        with open('/path/to/file/weatherdata.csv', 'a+') as f:
            if os.stat('/path/to/file/weatherdata.csv').st_size == 0:
                f.write('date,time,Temp (°C),Rain (mm),Wind Speed (km/h),Gust (km/h),Snow (mm)\r\n')

            f.write('{},{},{},{},{},{},{}\r\n'.format(time.strftime('%Y%m%d'), time.strftime('%H:%M'),
                                                     rounded_temp_celsius, rain, wind_speed_kmh, gust_kmh, snow))
    except Exception as e:
        print("Error writing to file:", e)

    # Create a dictionary to store the data
    data_temp = {
        'measurement': 'weather',
        'tags': {
            'location': 'Berlin'
        },
        'time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'fields': {
            'temp_celsius': rounded_temp_celsius,
            'rain_mm': float(rain),
            'windspeed_kmh': wind_speed_kmh,
            'gust_kmh': gust_kmh,
            'snow_mm': float(snow)
        }
    }

    # Convert the dictionary to Line Protocol
    line_protocol = f"{data_temp['measurement']},location={data_temp['tags']['location']} "
    line_protocol += f"temp_celsius={data_temp['fields']['temp_celsius']},rain_mm={data_temp['fields']['rain_mm']},windspeed_kmh={data_temp['fields']['windspeed_kmh']},gust_kmh={data_temp['fields']['gust_kmh']},snow_mm={data_temp['fields']['snow_mm']} {int(time.mktime(time.strptime(data_temp['time'], '%Y-%m-%dT%H:%M:%SZ')))*10**9}"

    # Write data to InfluxDB
    with InfluxDBClient(url=influx_url, token=influx_token, org=influx_org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=influx_bucket, record=line_protocol)

