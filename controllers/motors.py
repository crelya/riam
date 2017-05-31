import RPi.GPIO as GPIO
from time import sleep

Motor1A = 16
Motor1B = 18
Motor1E = 22

Motor2A = 19
Motor2B = 21
Motor2E = 23

def init():
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(Motor1A, GPIO.OUT)
    GPIO.setup(Motor1B, GPIO.OUT)
    GPIO.setup(Motor1E, GPIO.OUT)

    GPIO.setup(Motor2A, GPIO.OUT)
    GPIO.setup(Motor2B, GPIO.OUT)
    GPIO.setup(Motor2E, GPIO.OUT)


def forward(time):
    init()
    print "Going forwards"
    motor_right_forward()
    motor_left_forward()

    sleep(time)

    stop()
    return True


def backwards(time):
    init()
    print "Going backwards"

    motor_right_backwards()
    motor_left_backwards()

    sleep(time)

    stop()

    return True

def motor_right_forward():

    GPIO.output(Motor1A, GPIO.HIGH)
    GPIO.output(Motor1B, GPIO.LOW)
    GPIO.output(Motor1E, GPIO.HIGH)

def motor_right_backwards():

    GPIO.output(Motor1A, GPIO.LOW)
    GPIO.output(Motor1B, GPIO.HIGH)
    GPIO.output(Motor1E, GPIO.HIGH)

def motor_left_forward():

    GPIO.output(Motor2A, GPIO.LOW)
    GPIO.output(Motor2B, GPIO.HIGH)
    GPIO.output(Motor2E, GPIO.HIGH)

def motor_left_backwards():

    GPIO.output(Motor2A, GPIO.HIGH)
    GPIO.output(Motor2B, GPIO.LOW)
    GPIO.output(Motor2E, GPIO.HIGH)

def rotate(degrees):
    init()
    if degrees <= 90 and degrees >=0:
        motor_right_backwards()
        motor_left_forward()
    else:
        motor_right_forward()
        motor_left_backwards()

    seconds = time_for_degrees(degrees)

    sleep(seconds)
    stop()
    return True


def time_for_degrees(degrees):
    return 0.1 * degrees / 90

def stop():
    init()
    print "STOPPING MOTORS"
    GPIO.output(Motor1E, GPIO.LOW)
    GPIO.output(Motor2E, GPIO.LOW)
    GPIO.cleanup()