from RPLCD import i2c
import ifaddr
from time import sleep
import Adafruit_ADS1x15
import math
import bme280

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

while True:
    addrs = read_ip_addresses()
    for addr in addrs:
        lcd.write_string(addr)
        print(addr)
        sleep(1)
        lcd.clear()

    for i in range(0,10):
        temp_c, temp_f = read_internal_temperature()

        lcd.write_string("Int temp: ")
        lcd.write_string(str(temp_c))
        lcd.write_string(" C")
        lcd.cursor_pos = (1,0)
        lcd.write_string("Int temp: ")
        lcd.write_string(str(temp_f))
        lcd.write_string(" F")
        print("Int temp: ", temp_c, " C")
        print("Int temp: ", temp_f, " F")
        sleep(0.5)
        lcd.clear()

    for i in range(0,10):
        temp_c, temp_f = read_external_temperature()
        lcd.write_string("Ext temp: ")
        lcd.write_string(str(temp_c))
        lcd.write_string(" C")
        lcd.cursor_pos = (1,0)
        lcd.write_string("Ext temp: ")
        lcd.write_string(str(temp_f))
        lcd.write_string(" F")

        print("Ext temp: ", temp_c, " C")
        print("Ext temp: ", temp_f, " F")
        sleep(0.5)
        lcd.clear()

    for i in range(0,10):
        pressure = read_external_pressure()
        lcd.write_string("Ext pressure: ")
        lcd.write_string(str(pressure))
        lcd.write_string(" hPa")
        print("Pressure: ", pressure, " hPa")
        sleep(0.5)
        lcd.clear()

