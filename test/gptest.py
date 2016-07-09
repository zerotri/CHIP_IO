#!/usr/bin/python

import CHIP_IO.GPIO as GPIO
import time
import threading

DO_APEINT1_TEST = False
DO_APEINT3_TEST = False
DO_XIOP2_TEST = True

num_callbacks = 0


def myfuncallback(channel):
    global num_callbacks
    num_callbacks += 1
    print("CALLBACK LIKE DRAKE IN HOTLINE BLING")


loopfunction_exit = False


def loopfunction():
    print("LOOP FUNCTION")
    for i in xrange(4):
        if loopfunction_exit:
            break
        if i % 2:
            mystr = "SETTING CSID0 LOW (i=%d)" % i
            print(mystr)
            GPIO.output("CSID0", GPIO.LOW)
        else:
            mystr = "SETTING CSID0 HIGH (i=%d)" % i
            print(mystr)
            GPIO.output("CSID0", GPIO.HIGH)
        print("SLEEPING")
        time.sleep(1)

num_errs = 0

print("RUNNING GPIO SELF TEST")
GPIO.selftest(0)

print("\nVERIFYING SIMPLE FUNCTIONALITY")
GPIO.setup("GPIO1", GPIO.IN)
GPIO.setup("CSID0", GPIO.OUT, initial=GPIO.HIGH)
if (GPIO.input("GPIO1") != GPIO.HIGH):
    print(" A high output on CSI0 does not lead to a high input on XIO-P2.")
    print(" Perhaps you forgot to connect them?")
    num_errs += 1
else:
    print(" Able to use alternate names for GPIO")
GPIO.cleanup()

GPIO.setup("U14_15", GPIO.IN)  # XIO-P0
GPIO.setup("CSID0", GPIO.OUT, initial=GPIO.LOW)
if (GPIO.input("XIO-P2") != GPIO.LOW):
    print(" A low output on CSI0 does not lead to a low input on XIO-P2.")
    print(" Perhaps you forgot to connect them?")
    num_errs += 1
else:
    print(" Able to use Pin Header+Number for GPIO")
GPIO.cleanup()

GPIO.setup("XIO-P2", GPIO.IN)
GPIO.setup("U14_31", GPIO.OUT)  # CSID0

print("READING XIO-P2")
GPIO.output("CSID0", GPIO.HIGH)
assert(GPIO.input("XIO-P2") == GPIO.HIGH)

GPIO.output("CSID0", GPIO.LOW)
print "LOW", GPIO.input("GPIO1")
assert(GPIO.input("GPIO1") == GPIO.LOW)

print("SWAP GPIO WIRES FOR EDGE DETECTION TESTS AS NEEDED")
raw_input("PRESS ENTER WHEN READY TO START EDGE DETECTION TESTS")

# ==============================================
# EDGE DETECTION - AP-EINT1
if DO_APEINT1_TEST:
    print("\nSETTING UP RISING EDGE DETECTION ON AP-EINT1")
    GPIO.setup("AP-EINT1", GPIO.IN)
    GPIO.add_event_detect("AP-EINT1", GPIO.RISING)

    print("VERIFYING EDGE DETECT")
    f = open("/sys/class/gpio/gpio193/edge", "r")
    edge = f.read()
    f.close()
    assert(edge == "rising\n")
    GPIO.remove_event_detect("AP-EINT1")

# ==============================================
# EDGE DETECTION - AP-EINT3
if DO_APEINT3_TEST:
    print("\nSETTING UP BOTH EDGE DETECTION ON AP-EINT3")
    GPIO.setup("AP-EINT3", GPIO.IN)
    GPIO.add_event_detect("AP-EINT3", GPIO.BOTH)

    print("VERIFYING EDGE DETECT")
    f = open("/sys/class/gpio/gpio35/edge", "r")
    edge = f.read()
    f.close()
    assert(edge == "both\n")
    GPIO.remove_event_detect("AP-EINT3")

# ==============================================
# EDGE DETECTION - EXPANDED GPIO
if DO_XIOP2_TEST:
    print("\nSETTING UP FALLING EDGE DETECTION ON XIO-P2")
    GPIO.add_event_detect("XIO-P2", GPIO.FALLING, myfuncallback)

    print("VERIFYING EDGE DETECT")
    base = GPIO.get_gpio_base()
    gfile = "/sys/class/gpio/gpio%d/edge" % (base + 2)
    f = open(gfile, "r")
    edge = f.read()
    f.close()
    assert(edge == "falling\n")

# LOOP WRITING ON CSID0 TO HOPEFULLY GET CALLBACK TO WORK
print("WAITING FOR CALLBACKS")
loopfunction()
mystr = " num_callbacks = %d" % num_callbacks
print(mystr)

print("PRESS CONTROL-C TO EXIT IF SCRIPT GETS STUCK")
GPIO.remove_event_detect("XIO-P2")
try:
    # WAIT FOR EDGE
    t = threading.Thread(target=loopfunction)
    t.start()
    print("WAITING FOR EDGE")
    if DO_APEINT1_TEST:
        GPIO.wait_for_edge("AP-EINT1", GPIO.FALLING)
    if DO_APEINT3_TEST:
        GPIO.wait_for_edge("AP-EINT3", GPIO.FALLING)
    if DO_XIOP2_TEST:
        GPIO.wait_for_edge("XIO-P2", GPIO.FALLING)
    # THIS SHOULD ONLY PRINT IF WE'VE HIT THE EDGE DETECT
    print("WE'VE FALLEN LIKE COOLIO'S CAREER")
except:
    pass

print("Exit thread")
loopfunction_exit = True
t.join()  # Wait till the thread exits.
GPIO.remove_event_detect("XIO-P2")

print("\n** BAD DAY SCENARIOS **")
print(" ")
print("TESTING ERRORS THROWN WHEN SPECIFYING EDGE DETECTION ON UNAUTHORIZED GPIO")
GPIO.setup("CSID1", GPIO.IN)
try:
    GPIO.add_event_detect("CSID1", GPIO.FALLING, myfuncallback)
    print(" Oops, it did not throw an exception!  BUG!!!")
    num_errs += 1
except ValueError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass
except RuntimeError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass

print("TESTING ERRORS THROWN WHEN SETTING UP AN ALREADY EXPORTED GPIO")
try:
    GPIO.setup("CSID0", GPIO.LOW)
    print(" Oops, it did not throw an exception!  BUG!!!")
    num_errs += 1
except ValueError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass
except RuntimeError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass

print("TESTING ERRORS THROWN WHEN WRITING TO A GPIO NOT SET UP")
try:
    GPIO.output("CSID2", GPIO.LOW)
    print(" Oops, it did not throw an exception!  BUG!!!")
    num_errs += 1
except ValueError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass
except RuntimeError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass

print("TESTING ERRORS THROWN WHEN WRITING TO A SET UP GPIO WITH NO DIRECTION")
try:
    GPIO.output("CSID1", GPIO.LOW)
    print(" Oops, it did not throw an exception!  BUG!!!")
    num_errs += 1
except ValueError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass
except RuntimeError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass

print("TESTING ERRORS THROWN FOR ILLEGAL GPIO")
try:
    GPIO.setup("NOTUSED", GPIO.IN)
    print(" Oops, it did not throw an exception!  BUG!!!")
    num_errs += 1
except ValueError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass
except RuntimeError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass

print("TESTING ERRORS THROWN FOR NON-GPIO")
try:
    GPIO.setup("FEL", GPIO.IN)
    print(" Oops, it did not throw an exception!  BUG!!!")
    num_errs += 1
except ValueError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass
except RuntimeError, ex:
    mystr = " error msg = %s" % ex.args[0]
    print(mystr)
    pass

print("GPIO CLEANUP")
GPIO.cleanup()

mystr = "DONE: %d ERRORS" % num_errs
print(mystr)
