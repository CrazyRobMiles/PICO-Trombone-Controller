# Trombone controller
#

import board
import busio
import adafruit_vl53l4cd
import adafruit_vl53l0x
import time
import usb_hid
from digitalio import DigitalInOut, Direction, Pull

import adafruit_bmp280
from adafruit_hid.mouse import Mouse

mouse = Mouse(usb_hid.devices)


class Distance():

    def __init__(self):
        self.valuePos = 0
        self.valueTotal = 0
        self.rollingAverageLength = 5
        self.rollingValues = []

        print("Rolling average length:{}".format(self.rollingAverageLength))

        for i in range(0, self.rollingAverageLength):
            self.rollingValues.append(0)

    def distance_moved(self):
        new_pos = self.blockingWaitForValue()
        diff = new_pos - self.current_pos
        self.current_pos = new_pos
        return diff

    def start(self):
        pass

    def blockingWaitForAverage(self, timeout=1):
        distance = self.blockingWaitForValue(timeout=1)

        self.valueTotal = self.valueTotal + distance
        self.valueTotal = self.valueTotal - self.rollingValues[self.valuePos]
        self.rollingValues[self.valuePos] = distance
        self.valuePos = self.valuePos + 1
        if self.valuePos == self.rollingAverageLength:
            self.valuePos = 0
        return int(self.valueTotal/self.rollingAverageLength*10)

    def speed_test(self):
        readingCount = 0
        ot = time.time()
        while True:
            x = self.blockingWaitForValue()
            readingCount = readingCount + 1
            nt = time.time()
            if nt != ot:
                print(readingCount, x)
                readingCount = 0
                ot = nt

    def dump(self):
        while True:
            print(self.blockingWaitForValue())


class DistanceSensor_vl53l0x(Distance):
# https://docs.circuitpython.org/projects/vl53l0x/en/latest/
    def __init__(self, i2c):
        super(DistanceSensor_vl53l0x, self).__init__()
        self.vl53 = adafruit_vl53l0x.VL53L0X(i2c)
        self.vl53.inter_measurement = 10
        print("VL53L0X Starting")

    def start(self):
        super(DistanceSensor_vl53l0x, self).start()
        self.vl53.timing_budget = 10
        self.vl53.start_continuous()
        self.current_pos = self.blockingWaitForValue()

    def blockingWaitForValue(self, timeout=1):
        end = time.monotonic() + 1
        while not self.vl53.data_ready:
            if time.monotonic() > end:
                break
        if time.monotonic() > end:
            return -1
        else:
            return self.vl53.range


class DistanceSensor_vl53l4cd(Distance):
# https://docs.circuitpython.org/projects/vl53l4cd/en/latest/api.html#adafruit_vl53l4cd.VL53L4CD
    def __init__(self, i2c):
        super(DistanceSensor_vl53l4cd, self).__init__()
        self.vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)
        print("VL53L4CD Starting")

    def start(self):
        super(DistanceSensor_vl53l4cd, self).start()
        self.vl53.timing_budget = 10
        self.vl53.start_ranging()
        self.current_pos = self.blockingWaitForValue()

    def blockingWaitForValue(self, timeout=1):
        end = time.monotonic() + 1
        while not self.vl53.data_ready:
            if time.monotonic() > end:
                break
        if time.monotonic() > end:
            return -1
        else:
            self.vl53.clear_interrupt()
            return self.vl53.distance * 10


class PlaySensor():

    def __init__(self):
        pass

    def speed_test(self):
        readingCount = 0
        ot = time.time()
        while True:
            x = self.play_pressed()
            readingCount = readingCount + 1
            nt = time.time()
            if nt != ot:
                print(readingCount, x)
                readingCount = 0
                ot = nt

class DummyPlaySensor(PlaySensor):
    def __init__(self):
        super(DummyPlaySensor, self).__init__()

    def play_pressed(self):
        return False


class PressureSensor_BMP280(PlaySensor):

    def __init__(self, i2c):
        super(PressureSensor_BMP280, self).__init__()
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
        self.pressure_detect = 5
        self.base_pressure = self.bmp280.pressure

    def play_pressed(self):
        pressure_change = self.bmp280.pressure - self.base_pressure
        return pressure_change > self.pressure_detect


class ButtonPlaySensor(PlaySensor):

    def __init__(self, pin):
        super(ButtonPlaySensor, self).__init__()
        self.red_button = DigitalInOut(board.GP14)
        self.red_button.switch_to_input(pull=Pull.UP)

    def play_pressed(self):
        return self.red_button.value == False


i2c_sda = board.GP0
i2c_scl = board.GP1
i2c = busio.I2C(i2c_scl, i2c_sda)

# Select the distance sensor and play sensors that you are 
# using in your configuration by commenting out the 
# ones you're not using

distance = DistanceSensor_vl53l0x(i2c)
#distance = DistanceSensor_vl53l4cd(i2c)
distance.start()
# distance.dump()
#play = DummyPlaySensor()
play = ButtonPlaySensor(board.GP17)
#play = PressureSensor_BMP280(i2c)

mouse_down = False
readingCount = 0
ot = time.time()
old_dist = distance.blockingWaitForAverage()
# Adjust this value depending on taste for the amount of mouse movement when the controller is moved
speed = 0.4

while True:
    dist = distance.blockingWaitForAverage()
    if dist < 30:
        pass
    else:
        change = old_dist-dist
        mouse_dist = int(change*speed)
        if mouse_dist != 0:
            mouse.move(y=mouse_dist)
        if play.play_pressed():
            if mouse_down == False:
                mouse.press(Mouse.LEFT_BUTTON)
                print("toot")
                mouse_down = True
        else:
            if mouse_down == True:
                mouse.release(Mouse.LEFT_BUTTON)
                print("untoot")
                mouse_down = False
    old_dist = dist
    # This displays the update rate per second
    readingCount = readingCount + 1
    nt = time.time()
    if nt != ot:
        print(readingCount, dist)
        readingCount = 0
        ot = nt

