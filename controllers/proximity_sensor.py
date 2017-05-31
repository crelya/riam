import time
from subprocess import call
import RPi.GPIO as GPIO

Trig = 11
Echo = 13

def init():
    GPIO.setmode(GPIO.BOARD)



    GPIO.setup(Trig, GPIO.OUT)
    GPIO.setup(Echo, GPIO.IN)


def check_distance():
    init()

    GPIO.output(Trig, False)
    time.sleep(2*10**-6)
    GPIO.output(Trig, True)
    time.sleep(10*10**-6)
    GPIO.output(Trig, False)

    while GPIO.input(Echo) == 0:
        start = time.time()

    while GPIO.input(Echo) == 1:
        end = time.time()

    duration = (end - start) * 10**6
    distance = duration / 58

    print "%.2f" % distance
    return distance

# while True:
#     try:
#         detectarObstaculo()
#     except KeyboardInterrupt:
#         break


# print "Limpiando..."
# GPIO.cleanup()
# print "Acabado."
