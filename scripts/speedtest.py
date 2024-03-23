#!/usr/bin/env python3
import os
import json
import re
import subprocess
import time
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


influx_url="IP:PORT"
influx_org="org"
influx_token="ACCESS_TOKEN"
influx_bucket="BUCKET_NAME"

#Requires speedtest binaries (apt install speedtest-cli -y)
response = subprocess.Popen('/usr/bin/speedtest --accept-license --accept-gdpr', shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')

ping = re.search('Latency:\s+(.*?)\s', response, re.MULTILINE)
download = re.search('Download:\s+(.*?)\s', response, re.MULTILINE)
upload = re.search('Upload:\s+(.*?)\s', response, re.MULTILINE)
jitter = re.search('Latency:.*?jitter:\s+(.*?)ms', response, re.MULTILINE)

ping = ping.group(1)
download = download.group(1)
upload = upload.group(1)
jitter = jitter.group(1)


#Write measurments into local file 
##########################

try:
    f = open('/path/to/file/speedtest.csv', 'a+')
    if os.stat('/path/to/file/speedtest.csv').st_size == 0:
            f.write('Date,Time,Ping (ms),Jitter (ms),Download (Mbps),Upload (Mbps)\r\n')
except:
    pass

f.write('{},{},{},{},{},{}\r\n'.format(time.strftime('%m/%d/%y'), time.strftime('%H:%M'), ping, jitter, download, upload))

#Put measurements into JSON array 
#################################

speed_data = [
    {
        "measurement" : "internet_speed",
        "tags" : {
            "host": "raspberrypi"
         },
        "fields" : {
            "download": float(download),
            "upload": float(upload),
            "ping": float(ping),
            "jitter": float(jitter)
         }
     }
  ]


#Write data into InfluxDB
#########################

with InfluxDBClient(url=influx_url, token=influx_token, org=influx_org) as client:
  write_api = client.write_api(write_options=SYNCHRONOUS)
  write_api.write(bucket=influx_bucket, record=speed_data)
