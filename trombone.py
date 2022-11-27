import time
import board
import adafruit_hcsr04
import usb_hid
from adafruit_hid.mouse import Mouse

sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP2, echo_pin=board.GP3)
mouse = Mouse(usb_hid.devices)

oldDistance = sonar.distance
speed = 10.0
count=0
oldTime=time.time()

while True:
    try:
        newDistance = sonar.distance
    except RuntimeError:
        continue
    delta = newDistance - oldDistance;
    mouse.move(0,int(delta*speed))
    oldDistance = newDistance
    count=count+1
    newTime = time.time()
    if newTime!=oldTime:
        print(count)
        count=0
        oldTime=newTime
        
        


