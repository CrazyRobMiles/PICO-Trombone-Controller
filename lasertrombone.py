import time
import board
import busio
import usb_hid
import adafruit_vl53l0x
import random

from adafruit_hid.mouse import Mouse

mouse = Mouse(usb_hid.devices)

# Make i2c connection
i2c_sda=board.GP0
i2c_scl=board.GP1

i2c = busio.I2C(i2c_scl, i2c_sda)
sensor = adafruit_vl53l0x.VL53L0X(i2c)
sensor.measurement_timing_budget = 20000

oldDistance = sensor.range
speed = 3
count=0
rollingAverageLength = 30
oldTime=time.time()

rollingValues=[]
for i in range(0,rollingAverageLength):
    rollingValues.append(0)

valuePos = 0
valueTotal = 0

while True:
    try:
        newDistance = sensor.range
    except RuntimeError:
        continue
    delta = newDistance - oldDistance
    #delta = 5 + ((random.random()*2)-1)
    valueTotal = valueTotal + delta
    valueTotal = valueTotal - rollingValues[valuePos]
    rollingValues[valuePos] = delta
    valuePos = valuePos + 1
    if valuePos == rollingAverageLength:
        valuePos = 0
    smoothedDelta = int(valueTotal/rollingAverageLength)
    print(delta,smoothedDelta)
    mouse.move(0,int(delta*speed))
    oldDistance = newDistance
    count=count+1
    newTime = time.time()
    if newTime!=oldTime:
        print(count)
        count=0
        oldTime=newTime
        
        


