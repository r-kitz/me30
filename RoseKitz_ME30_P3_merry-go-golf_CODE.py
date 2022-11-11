# Rose Kitz
# ME30
# Project 3: Build an electromechanical game
# Instructors Kristen Wendell & Brandon Stafford
# 11/10/2022

# stepper motor/h-bridge help from:
    # https://learn.adafruit.com/adafruit-stepper-dc-motor-featherwing/circuitpython
    # SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
    # SPDX-License-Identifier: MIT

import board
import analogio # for pots
import digitalio
import pwmio # for variable (digital) signal to DC motor (based on analog input of pot)
from adafruit_motor import stepper
import time

# initialize input analog pins
pin_a0 = analogio.AnalogIn(board.A0) # pot for speed
pin_a1 = analogio.AnalogIn(board.A1) # pot for swing angle
pin_a2 = analogio.AnalogIn(board.A2) # pot for course difficulty (DC motor/platform speed)
duty_max = 65535 # global

# initialize output digital pins to V_A and V_B of DC motor h-bridge
pin_va = pwmio.PWMOut(board.TX)
pin_vb = pwmio.PWMOut(board.D4)

# set duty cycles for DC motor voltage inputs to zero before start so motor is off
pin_va.duty_cycle = 0
pin_vb.duty_cycle = 0

# initialize output digital pins to indicator LEDs (swing angle or speed selector)
# could have implemented PWM as next step so LEDs dim/brighten as angle/speed change
angle_pot_led = digitalio.DigitalInOut(board.D24)
angle_pot_led.direction = digitalio.Direction.OUTPUT
speed_pot_led = digitalio.DigitalInOut(board.D25)
speed_pot_led.direction = digitalio.Direction.OUTPUT

# set indicator LEDs off to start code
angle_pot_led.value = False
speed_pot_led.value = False

# set up setup (set swing angle and speed) button (small white pushbutton)
button_setup = digitalio.DigitalInOut(board.D5)
button_setup.direction = digitalio.Direction.INPUT
button_setup.pull = digitalio.Pull.UP

# set up take swing button (big arcade button)
button_swing = digitalio.DigitalInOut(board.D6)
button_swing.direction = digitalio.Direction.INPUT
button_swing.pull = digitalio.Pull.UP

# --- SET UP STATE MACHINE ---
# initialize timer variables
toggle_wait = 0.01
next_big_check = 0 # timer variable to move small check to big check
next_setup = 0 # timer variable to move big check to setup

# initialize state variables to toggle between
# there are two levels of states (1 & 2) to track button presses/toggle with setup, and within setup, toggle between setting swing angle and speed
STATE_SETUP = 1 # option for state1
STATE_CHECK_SMALL_BUTTON = 2 # option for state1
STATE_CHECK_BIG_BUTTON = 3 # option for state1
STATE_SET_SWING_ANGLE = 4 # option for state2 ('inner' state)
STATE_SET_SWING_SPEED = 5 # option for state2 ('inner' state)

# initialize values of each of the two levels of states
state1 = STATE_SETUP # initialize outer state as setup
state2 = STATE_SET_SWING_ANGLE # initialize inner state as swing angle

# set time motor runs for each step
# suggested 0.01 (Adafruit), as short as 0.005 if needed
# --- CHANGES SPEED OF MOTOR ---
MIN_DELAY = 0.005
MAX_DELAY = MIN_DELAY * 6 # 0.03

# set # of steps needed for motor to rotate once around
# 200 full steps for 360-deg rotation of ME30 kit stepper(or 400 half steps [INTERLEAVE])
# --- CHANGES HOW FAR MOTOR TURNS ---
STEPS = 200
MAX_SWING_ANGLE = STEPS / 2 # max can swing back from 0 is half a revolution
MIN_SWING_ANGLE = 5 # set minimum angle to swing as 5 so the putter moves at least a little bit
user_swing_angle = 0 # initialize global
user_delay = 0 # initialize global

HOME_POS = 0 # set value of home angle position of motor as zero (to track and reset later)
current_position = 0 # initialize variable to track current position, to later reset

# assign motor coils to digital feather pins
coils = (
    digitalio.DigitalInOut(board.D9),  # A1
    digitalio.DigitalInOut(board.D10),  # A2
    digitalio.DigitalInOut(board.D11),  # B1
    digitalio.DigitalInOut(board.D12),  # B2
)

print("coils initialized")

for coil in coils:
    coil.direction = digitalio.Direction.OUTPUT

# create motor object w/ wiring details, using stepper command from adafruit_motor library

motor = stepper.StepperMotor(coils[0], coils[1], coils[2], coils[3], microsteps=None)

print("motor initialized")

# --- FUNCTIONS ---

# function (finicky) to attempt to 'home' the angle of the stepper motor shaft so putter restarts at bottom with every attempt
def to_home_position(current_pos):
    steps_away = current_pos - HOME_POS # HOME_POS is currently 0, but included this in case I change it later so the function still works

    for step in range(steps_away):
            motor.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            time.sleep(MIN_DELAY)

# function to measure current 'course difficulty' pot value and map to DC motor voltage to run motor at variable speeds in one direction
# extension idea: create harder difficulty levels so platform randomly changes speed & direction, rather than using pot input
# simpler idea: hardcode slow speed of motor (had trouble achieving low speed with readings from pot, even with attempt to scale down)
def run_dc():
    # get input voltage from dc pot
    dc_current_input = pin_a2.value # not scaled to Volts
    # 65536 is one above max duty cycle (analog input is on scale of max duty cycle!)
    dc_input_voltage = (dc_current_input * 3.3) / duty_max # now it's a voltage on scale of 0-3.3 (not necessary step but easier conceptually than just dividing by 65536 to get a %
    #print("input", input_voltage)

    # SEND variable input voltage to motor to change speed (scale to 12V!)
    dc_speed_percent = (dc_input_voltage / 3.3) # kind of just undoing the conversion I did above...LOL. but wanna print input voltage
    #print("%", speed_percent)

    # make sure vb is OFF before turning va ON (should be off based on code before, best to double check so don't short circuit)
    pin_vb.duty_cycle = 0
    # turn on va pin
    pin_va.duty_cycle = int(dc_speed_percent * duty_max) # cast b/c duty cycle must be an integer

# function takes input from 'angle' pot to change position of putter on stepper shaft in real time as the user chooses the angle to start their swing at
def set_swing_angle():
    # GET INPUT VOLTAGE from pot and translate to swing angle
    current_input = pin_a1.value # not scaled to Volts
    angle_percent = current_input / duty_max # higher % = higher speed, lower % = lower speed
    #print(angle_percent)

    # swing% directly relates to swing angle (higher percentage, higher angle)
    global user_swing_angle
    user_swing_angle = int((angle_percent * (MAX_SWING_ANGLE - MIN_SWING_ANGLE)) + MIN_SWING_ANGLE) # cast to int so only integer steps

    # swing to show current selected position
    # move back if chosen angle is greater than current
    global current_position
    if user_swing_angle > current_position:
        for step in range(user_swing_angle - current_position):
            # motor backward, single style (not much torque needed)
            motor.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
            time.sleep(MIN_DELAY)
    # move forward if chosen angle is less than current
    elif user_swing_angle < current_position: # if current position is greater than chosen (difference of chosen from current is negative, need to moves towards zero)
        for step in range(current_position - user_swing_angle):
            # motor forward, single style (not much torque needed)
            motor.onestep(direction=stepper.FORWARD, style=stepper.SINGLE)
            time.sleep(MIN_DELAY)
    current_position = user_swing_angle
    # if diff is 0, don't adjust!

# function takes input from 'speed' pot to select speed of swing
def set_swing_speed():
    # GET INPUT VOLTAGE from pot and translate to % for swing speed
    current_input = pin_a0.value # not scaled to Volts
    speed_percent = current_input / duty_max # higher % = higher speed, lower % = lower speed
    #print(speed_percent)

    # set speed of motor (delay between steps)
    # earlier: MIN_DELAY = 0.005 , related to max speed of motor
    # convert high % for high speed to opposite, so map to range of min delay (max speed) to max delay (min speed)
    # so if speed_percent=1, user_delay = MIN_DELAY
    # if speed_percent=0, user_delay = MAX_DELAY
    global user_delay
    user_delay = ((1 - speed_percent) * (MAX_DELAY - MIN_DELAY)) + MIN_DELAY

# function triggered by arcade button press, to move stepper motor so the putter swings fully forward and back to original position
def take_swing():
    # user_swing_angle is global

    # swing forward (2x user angle)
    full_swing = 2 * user_swing_angle
    for step in range(full_swing):
        # motor forward, double style for more torque
        motor.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
        time.sleep(user_delay)

    # swing back to current user_swing_angle
    for step in range(full_swing):
        # motor backward, single style (not much torque needed)
        motor.onestep(direction=stepper.BACKWARD, style=stepper.SINGLE)
        time.sleep(user_delay)


# set tracker variables for buttons so later, actions only happen once in reaction to a button press (i.e. aren't repeated if button is held and keeps checking as held)
was_small_pressed = False
was_big_pressed = True

is_start = True # variable to tell later in code for something to run only when the code restarts

while True:

    run_dc()

    # --- CAN SET SWING ANGLE AND SPEED ANY TIME THAT A SWING ISN'T GOING
    # set swing angle (loop until press button to move on [loop while button is not pressed and wasn't pressed before])
    # swing angle = angle from 0 (down) to 180deg (putter starts pointing completely upwards)
    if state1 is STATE_SETUP:
        if state2 is STATE_SET_SWING_ANGLE:
            # turn swing angle LED on to indicate that swing angle can be changed right now
            angle_pot_led.value = True

            set_swing_angle()

            # note: only turn off led when small button is pressed later to change state2 (so led stays on until state2 is changed, rather than turning off each time the while loop runs this if statement even when state2 doens't change

            #print(user_swing_angle)
        elif state2 is STATE_SET_SWING_SPEED:

            speed_pot_led.value = True

            set_swing_speed()
            #print(user_delay)

        next_big_check = time.monotonic() + toggle_wait
        state1 = STATE_CHECK_SMALL_BUTTON

    elif state1 is STATE_CHECK_SMALL_BUTTON:
        if button_setup.value == 0 and (not was_small_pressed): # 0 is pressed from experiments
            if state2 is STATE_SET_SWING_ANGLE:
                # if state2 changes from last time, turn off last led (new one will turn on when state runs)
                # didn't turn off inside the respective states, b/c then EACH time this while loop runs the led will blink b/c will turn off, go to other state1's, then if state2 doens't change, go back and turn back on and BLINK (not sure if I desire blinking, want static LED)
                angle_pot_led.value = False # turn led off (although I think might blink b/c changing state1, even if
                state2 = STATE_SET_SWING_SPEED
            else: # state2 is currently swing speed
                speed_pot_led.value = False # turn led off
                state2 = STATE_SET_SWING_ANGLE
            was_small_pressed = True
        if button_setup.value == 1:
            was_small_pressed = False # change tracker to False if button is released

        if time.monotonic() > next_big_check:
            state1 = STATE_CHECK_BIG_BUTTON

        next_setup = time.monotonic() + 0.01 # wait 0.01 second to check big button

    elif state1 is STATE_CHECK_BIG_BUTTON:
        if button_swing.value == 0 and (not was_big_pressed): # 0 is pressed
            # (if running swing function, swing must complete before moving on to next state!)
            take_swing()

            # turn both indicator leds off, in case they are on
            angle_pot_led.value = False
            speed_pot_led.value = False

            state2 = STATE_SET_SWING_ANGLE # reset to default to start at angle after a swing
            was_big_pressed = True
        # check if button is released to reset if was just pressed or not
        if button_swing.value == 1:
            was_big_pressed = False
        if time.monotonic() > next_setup:
            state1 = STATE_SETUP
    # not sure if need current pos home here

motor.release() # won't actually run b/c it's outside while True...
