from RPLCD import i2c
#import RPi.GPIO as GPIO
import ifaddr
from time import sleep

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

def readIPaddresses():
    adapters = ifaddr.get_adapters()

    addrs = []
    for adapter in adapters:
        for ip in adapter.ips:
            addrs.append(ip.ip)

    return addrs

while True:
    addrs = readIPaddresses()
    for addr in addrs:
        lcd.write_string(addr)
        sleep(1)
        lcd.clear()
        sleep(0.1)
