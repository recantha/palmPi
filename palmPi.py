# palmPi code written by Michael Horne
# @recantha
# www.recantha.co.uk/blog
# March 2018

# import libraries
from RPLCD import i2c
import ifaddr
from time import sleep, strftime
import Adafruit_ADS1x15
import math
import bme280
from gpiozero import LED, Button
from subprocess import call
from ISStreamer.Streamer import Streamer
import threading
from twython import Twython
from auth import (consumer_key, consumer_secret, access_token, access_token_secret)

# Function to return IP address list
def read_ip_addresses():
    adapters = ifaddr.get_adapters()

    addrs = []
    for adapter in adapters:
        for ip in adapter.ips:
            addrs.append(ip.ip)

    return addrs

# Function to use ADC to read temperature from TMP36 and convert it to C and F
def read_internal_temperature():
    ADC_GAIN = 2
    adc_reading = adc.read_adc(0, gain=ADC_GAIN)
    adc_mv = ((adc_reading * 2.048)/2048) * 1000

    temp_c = (adc_mv - 500) / 10
    temp_f = (temp_c * 1.8) + 32

    return "{:+.2f}".format(temp_c), "{:+.2f}".format(temp_f)

# Function to read temperature from BMP280 and convert it to F
def read_external_temperature():
    temp_c,pressure,humidity = bme280.readBME280All()
    temp_f = (temp_c * 1.8) + 32

    return "{:+.2f}".format(temp_c), "{:+.2f}".format(temp_f)

# Function to read pressure from BMP280
def read_external_pressure():
    temperature,pressure,humidity = bme280.readBME280All()
    pressure = "{:.2f}".format(pressure)
    return pressure

# Wrapper for manual shutdown
def shutdown_manual():
    shutdown("Manual")

# Wrapper for battery warning shutdown
def shutdown_battery_warning():
    shutdown("Battery")

# Actual shutdown function
def shutdown(reason):
    shutting_down = True
    twitter_status = get_timestamp() + " - Shutting down - " + reason
    twitter.update_status(status=twitter_status)

    lcd.clear()
    lcd.write_string('Shutting down')
    sleep(2)
    lcd.clear()

    lcd.write_string(reason)
    red_button_led.blink(n=5)
    sleep(2)
    call("sudo shutdown -h now", shell=True)
    exit(1)

# Streamer log wrapper
def streamer_log(type, value):
    if streamer_started:
        streamer.log(type, value)
    else:
        print("Not streaming value ", type, "=", value)

# Class to extend threading.Thread so we can start up the new streaming thread
class readingThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.daemon = True

    def run(self):
        print ("Starting " + self.name)
        print("Streaming readings")
        stream_readings()
        print ("Exiting " + self.name)

# Get sensor readings and send to the streamer
def stream_readings():
    while True:
        i_temp_c, i_temp_f = read_internal_temperature()
        e_temp_c, e_temp_f = read_external_temperature()
        e_pressure = read_external_pressure()
        print("Streaming temps")
        streamer_log("Internal temp C", i_temp_c)
        streamer_log("Internal temp F", i_temp_f)
        streamer_log("External temp C", e_temp_c)
        streamer_log("External temp F", e_temp_f)
        print("Streaming pressure")
        streamer_log("Pressure", e_pressure)
        streamer.flush()

        try:
            twitter_status = get_timestamp() + " - Int temp: " + str(i_temp_c) + "C / Ext temp:" + str(e_temp_c) + "C / Pressure: " + str(e_pressure) + "hPa"
            twitter.update_status(status=twitter_status)
        except:
            print("Twython did not tweet")

        print("Sleeping for 15 minutes")
        sleep(900)

# Twitter detects repetition, so timestamp the tweets to prevent them reading as duplicates
def get_timestamp():
    timestamp = strftime("%Y%m%d-%H:%M:%S")

    return timestamp

try:
    twitter = Twython(consumer_key, consumer_secret, access_token, access_token_secret)
    twitter_status = "palmPi started up at " + get_timestamp()
    twitter.update_status(status=twitter_status)

except:
    print("Twython did not tweet")

# Start up the ADC
adc = Adafruit_ADS1x15.ADS1015()

# Set flag for when the palmPi is being shut down to prevent LCD clashes
shutting_down = False

# Instantiate the LCD
lcdmode = 'i2c'
cols = 16
rows = 2
charmap = 'A00'
i2c_expander = 'PCF8574'
address = 0x3f
port = 1 # 0 on an older Pi

lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                  cols=cols, rows=rows)
lcd.clear()

# Define the momentary, illuminated button
red_button_led = LED(18)
red_button = Button(17)
red_button_led.on()

# Pick up when the PowerBoost 1000C alerts a battery warning. Do it as a Button, though should just be a generic input device
battery_warning = Button(4)
battery_warning.when_pressed = shutdown_battery_warning

lcd.write_string("palmPi started")
sleep(1)
lcd.clear()

# Streamer constructor, this will create a bucket called Python Stream Example
# you'll be able to see this name in your list of logs on initialstate.com
# your access_key is a secret and is specific to you, don't share it!
try:
    streamer = Streamer(bucket_name="palmPi", bucket_key="WQ44PMQYULFV", access_key="y8ZCpNZ5ZYQQLfU5zKqdZrSEyizKFc17", debug_level=0)
    streamer_started = True
    print("Streamer started")
    lcd.write_string("Streamer started")

except:
    lcd.write_string("Streamer not started")
    streamer_started = False

sleep(1)
lcd.clear()

# Start up the 15-minute looping thread for streaming and tweeting readings
thread_readings = readingThread(1, "Reading-Thread", 1)
thread_readings.start()

while True:
    # If button is pressed when it gets to this point, shutdown palmPi
    if red_button.is_pressed:
        shutdown_manual()

    # if flag is not set, get readings and spit them out onto LCD
    if not shutting_down:
        # Show the IP addresses of palmPi
        addrs = read_ip_addresses()
        for addr in addrs:
            lcd.write_string(addr)
            print(addr)
            sleep(1)
            lcd.clear()

        # Read and display internal temperature
        for i in range(0,10):
            temp_c, temp_f = read_internal_temperature()

            lcd.write_string("Int: ")
            lcd.write_string(str(temp_c))
            lcd.write_string("C")
            lcd.cursor_pos = (1,0)
            lcd.write_string("Int: ")
            lcd.write_string(str(temp_f))
            lcd.write_string("F")
            print("Int temp: ", temp_c, " C")
            print("Int temp: ", temp_f, " F")

            sleep(0.5)
            lcd.clear()
 
        # Read and display external temperature
        for i in range(0,10):
            temp_c, temp_f = read_external_temperature()
            lcd.write_string("Ext: ")
            lcd.write_string(str(temp_c))
            lcd.write_string("C")
            lcd.cursor_pos = (1,0)
            lcd.write_string("Ext: ")
            lcd.write_string(str(temp_f))
            lcd.write_string("F")

            print("Ext temp: ", temp_c, " C")
            print("Ext temp: ", temp_f, " F")

            sleep(0.5)
            lcd.clear()

        # Read and display external pressure reading
        for i in range(0,10):
            pressure = read_external_pressure()
            lcd.write_string("Pres: ")
            lcd.write_string(str(pressure))
            lcd.write_string("hPa")
            print("Pressure: ", pressure, " hPa")

            sleep(0.5)
            lcd.clear()

