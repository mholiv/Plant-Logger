import Adafruit_DHT
import RPi.GPIO as GPIO
import boto3
import datetime
import time
from decimal import Decimal

pin = 17

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
temp_humid_log_table = dynamodb.Table('soil_temperature_humidity_log')
heat_pad_status_log_table = dynamodb.Table('heat_pad_status_log')

sensor = Adafruit_DHT.DHT22
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

# We first turn on the heat pad
GPIO.output(18, True)
heat_pad_on = True

def write_heat_pad_log(switched_to, temperature):
    heat_pad_status_log_table.put_item(
                Item={
                    'plant': 'pepper_flat_0',
                    'iso_date_time': datetime.datetime.now().isoformat(),
                    'date_time': Decimal(int(time.time())),
                    'heat_pad_power_changed_to': Decimal(switched_to),
                    'temprature': Decimal('{0:0.1f}'.format(temperature)),
                }
            )

while True:
    try:

        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

        if humidity is not None and temperature is not None:
            print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            temp_as_dec = Decimal(temperature)

            temp_humid_log_table.put_item(
                Item={
                    'plant': 'pepper_flat_0',
                    'iso_date_time': datetime.datetime.now().isoformat(),
                    'date_time': Decimal(int(time.time())),
                    'temprature': Decimal('{0:0.1f}'.format(temperature)),
                    'humidity': Decimal('{0:0.1f}'.format(humidity)),
                }
            )

            if temp_as_dec <= Decimal(28.5):
                if not heat_pad_on:
                    GPIO.output(18, True)
                    heat_pad_on = True
                    write_heat_pad_log(1, temperature)
            if temp_as_dec >= Decimal(30.5):
                if heat_pad_on:
                    GPIO.output(18, False)
                    heat_pad_on = False
                    write_heat_pad_log(0, temperature)


        else:
            print('Failed to get reading. Try again!')
    except Exception as e:
        print(e)

    time.sleep(120)
