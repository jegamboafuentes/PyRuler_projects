import os
import board
from digitalio import DigitalInOut, Direction
import time
import touchio
import busio
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Set this to True to turn the touchpads into a keyboard
ENABLE_KEYBOARD = True

WINDOWS = "W"
MAC = "M"
LINUX = "L"  # and Chrome OS

# Set your computer type to one of the above
OS = WINDOWS

# Used if we do HID output, see below
if ENABLE_KEYBOARD:
    kbd = Keyboard()
    layout = KeyboardLayoutUS(kbd)

led = DigitalInOut(board.D13)
led.direction = Direction.OUTPUT

touches = [DigitalInOut(board.CAP0)]
for p in (board.CAP1, board.CAP2, board.CAP3):
    touches.append(touchio.TouchIn(p))

leds = []
for p in (board.LED4, board.LED5, board.LED6, board.LED7):
    led = DigitalInOut(p)
    led.direction = Direction.OUTPUT
    led.value = True
    time.sleep(0.25)
    leds.append(led)
for led in leds:
    led.value = False

cap_touches = [False, False, False, False]

# Setup SPI for DotStar
spi = busio.SPI(board.APA102_SCK, MOSI=board.APA102_MOSI)
while not spi.try_lock():
    pass
spi.configure(baudrate=4000000)

# Create a bytearray to store the frame
frame = bytearray(12)
# Start frame is all zeros
frame[0:4] = bytes([0, 0, 0, 0])
# LED frame starts with 111 (brightness control) and ends with the RGB values
frame[4:8] = bytes([0xFF, 0, 0, 0])
# End frame is all ones
frame[8:12] = bytes([0xFF, 0xFF, 0xFF, 0xFF])
# Send the frame to the DotStar LED
spi.write(frame)
# Unlock the SPI now that we're done
spi.unlock()

# ... Rest of your code ...
def read_caps():
    t0_count = 0
    t0 = touches[0]
    t0.direction = Direction.OUTPUT
    t0.value = True
    t0.direction = Direction.INPUT
    # funky idea but we can 'diy' the one non-hardware captouch device by hand
    # by reading the drooping voltage on a tri-state pin.
    t0_count = t0.value + t0.value + t0.value + t0.value + t0.value + \
               t0.value + t0.value + t0.value + t0.value + t0.value + \
               t0.value + t0.value + t0.value + t0.value + t0.value
    cap_touches[0] = t0_count > 2
    cap_touches[1] = touches[1].raw_value > 3000
    cap_touches[2] = touches[2].raw_value > 3000
    cap_touches[3] = touches[3].raw_value > 3000
    return cap_touches

def type_alt_code(code):
    kbd.press(Keycode.ALT)
    for c in str(code):
        if c == '0':
            keycode = Keycode.KEYPAD_ZERO
        elif '1' <= c <= '9':
            keycode = Keycode.KEYPAD_ONE + ord(c) - ord('1')
        else:
            raise RuntimeError("Only number codes permitted!")
        kbd.press(keycode)
        kbd.release(keycode)
    kbd.release_all()

cc = ConsumerControl()

while True:
    caps = read_caps()
    print(caps)
    # light up the matching LED
    for i,c in enumerate(caps):
        leds[i].value = c
    if caps[0]:
        if ENABLE_KEYBOARD:
            if OS == WINDOWS:
                #type_alt_code(234)
                #type_alt_code(129297)
                cc.send(ConsumerControlCode.VOLUME_DECREMENT)
            elif OS == MAC:
                kbd.send(Keycode.ALT, Keycode.Z)
            elif OS == LINUX:
                kbd.press(Keycode.CONTROL, Keycode.SHIFT)
                kbd.press(Keycode.U)
                kbd.release_all()
                kbd.send(Keycode.TWO)
                kbd.send(Keycode.ONE)
                kbd.send(Keycode.TWO)
                kbd.send(Keycode.SIX)
                kbd.send(Keycode.ENTER)
    if caps[1]:
        if ENABLE_KEYBOARD:
            if OS == WINDOWS:
                #type_alt_code(230)
                cc.send(ConsumerControlCode.VOLUME_INCREMENT)
            elif OS == MAC:
                kbd.send(Keycode.ALT, Keycode.M)
            elif OS == LINUX:
                kbd.press(Keycode.CONTROL, Keycode.SHIFT)
                kbd.press(Keycode.U)
                kbd.release_all()
                kbd.send(Keycode.ZERO)
                kbd.send(Keycode.THREE)
                kbd.send(Keycode.B)
                kbd.send(Keycode.C)
                kbd.send(Keycode.ENTER)
    if caps[2]:
        if ENABLE_KEYBOARD:
            if OS == WINDOWS:
                #type_alt_code(227)
                cc.send(ConsumerControlCode.MUTE)
            elif OS == MAC:
                kbd.send(Keycode.ALT, Keycode.P)
            elif OS == LINUX:
                kbd.press(Keycode.CONTROL, Keycode.SHIFT)
                kbd.press(Keycode.U)
                kbd.release_all()
                kbd.send(Keycode.ZERO)
                kbd.send(Keycode.THREE)
                kbd.send(Keycode.C)
                kbd.send(Keycode.ZERO)
                kbd.send(Keycode.ENTER)
    if caps[3]:
        if ENABLE_KEYBOARD:
            kbd.send(Keycode.ALT, Keycode.A)
            #layout.write('https://www.digikey.com/python\n')
            #layout.write('metaverseprofessional.tech')
    time.sleep(0.1)
