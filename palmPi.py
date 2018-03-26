from RPLCD import i2c
import ifaddr
from time import sleep
import Adafruit_ADS1x15
import math
import bme280
from gpiozero import LED, Button
from subprocess import call
from ISStreamer.Streamer import Streamer
import threading

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

red_button_led = LED(18)
red_button = Button(17)

def read_ip_addresses():
    adapters = ifaddr.get_adapters()

    addrs = []
    for adapter in adapters:
        for ip in adapter.ips:
            addrs.append(ip.ip)

    return addrs

adc = Adafruit_ADS1x15.ADS1015()

def read_internal_temperature():
    ADC_GAIN = 2
    adc_reading = adc.read_adc(0, gain=ADC_GAIN)
    adc_mv = ((adc_reading * 2.048)/2048) * 1000

    temp_c = (adc_mv - 500) / 10
    temp_f = (temp_c * 1.8) + 32

    return "{:+.2f}".format(temp_c), "{:+.2f}".format(temp_f)

def read_external_temperature():
    temp_c,pressure,humidity = bme280.readBME280All()
    temp_f = (temp_c * 1.8) + 32

    return "{:+.2f}".format(temp_c), "{:+.2f}".format(temp_f)

def read_external_pressure():
    temperature,pressure,humidity = bme280.readBME280All()
    pressure = "{:.2f}".format(pressure)
    return pressure

shutting_down = False
def shutdown():
    shutting_down = True
    lcd.clear()
    lcd.write_string('Shutting down')
    red_button_led.blink(n=5)
    sleep(3)
    call("sudo shutdown -h now", shell=True)
    exit(1)

def streamer_log(type, value):
    if streamer_started:
        streamer.log(type, value)
    else:
        print("Not streaming value ", type, "=", value)

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

        print("Sleeping for 15 minutes")
        sleep(900)

red_button_led.on()

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

thread_readings = readingThread(1, "Reading-Thread", 1)
thread_readings.start()

while True:
    if red_button.is_pressed:
        shutdown()

    if not shutting_down:
        addrs = read_ip_addresses()
        for addr in addrs:
            lcd.write_string(addr)
            print(addr)
            sleep(1)
            lcd.clear()

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

        for i in range(0,10):
            pressure = read_external_pressure()
            lcd.write_string("Pres: ")
            lcd.write_string(str(pressure))
            lcd.write_string("hPa")
            print("Pressure: ", pressure, " hPa")

            sleep(0.5)
            lcd.clear()

