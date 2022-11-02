# Rose Kitz
# ME30
# 11/1/22
# P3 prototype - controlling motor direction with P2 Hbridge and potentiometer to create 'mini golf swing'

# STATUS
# button press to make motor spin forward and backward once. need to release and press again for motor to move again.
# NEXT: switch to stepper for angle control, or figure out a way to calculate a revolution with speed...but not super precise though perhaps more b/c rotation is controlled by code
# --- maybe change time runs (longer time for slower speed, shorter time for higher speed to get same revolution)
# ----- programmed automatic swing and return to back position so user doesn't have to change direction of the swing, just press button to 'do' swing

import board
import analogio # for pot
import digitalio
import pwmio # for variable (digital) signal to motor (based on analog input of pot)
import time

print("test")

# initialize input analog pot pin
pin_a0 = analogio.AnalogIn(board.A0)
# initialize output digital pins to V_A and V_B of hbridge
pin_d5 = pwmio.PWMOut(board.D5)
pin_d6 = pwmio.PWMOut(board.D6) # will PWM work w hbridge? cuz we learned use 0/3.3 to turn off/on but how to turn to diff speed off/on in diff directions?

# Mode button setup
button_swing = digitalio.DigitalInOut(board.D9)
button_swing.direction = digitalio.Direction.INPUT
button_swing.pull = digitalio.Pull.UP
#button_state = False  # track state of button mode (True is on, False is off)

pin_d5.duty_cycle = 0
pin_d6.duty_cycle = 0 # set zero before start so motor is off (IS THIS NECESSARY??? or does this default w/o this line?)

duty_max = 65535 # for some reason CircuitPython converts input analog (below inside while True) with 65536...why?

speed_percent = 0 # initialize

state_direction = 'forward'

count_loops = 0

# track button state
was_pressed = False

time_swing = 0.5

while True:
    '''
    # check if time to change motor direction
    if count_loops > 9: # run loop 10 times before switching direction (count_loops starts at 0)
        if state_direction == 'forward':
            state_direction = 'backward'
        else: # 'backward'
            state_direction = 'forward'

        count_loops = 0 # reset counter
    '''
    # only take potentiometer value and set motor on if button is pressed

    # if button is pressed and wasn't pressed on last loop
    if button_swing.value == 0 and (not was_pressed): # from experiment, 0 is pressed; only run loop once after a singular button press

        # GET INPUT VOLTAGE from pot
        current_input = pin_a0.value # not scaled to Volts
        # 65536 is one above max duty cycle (analog input is on scale of max duty cycle!
        input_voltage = (current_input * 3.3) / duty_max # now it's a voltage on scale of 0-3.3 (not necessary step but easier conceptually than just dividing by 65536 to get a %
        #print("input", input_voltage)

        # SEND variable input voltage to motor to change speed (scale to 12V!)
        speed_percent = (input_voltage / 3.3) # kind of just undoing the conversion I did above...LOL. but wanna print input voltage
        print("%", speed_percent)

        #if state_direction == 'forward':

        # --- move putter forward for 1 second to swing ---
        # turn off pin D5 -- MUST do before turning pin on so both H-bridge pins aren't on at the same time
        pin_d5.duty_cycle = 0
        # turn on pin D6

        pin_d6.duty_cycle = int(speed_percent * duty_max) # cast b/c duty cycle must be an integer

            #state_direction = 'backward'
        time.sleep(time_swing) # wait

        # --- move putter backward to reset for next swing (NEED to adjust for position...)
        #else: # 'backward'
        # turn off pin D6
        pin_d6.duty_cycle = 0
        # turn on pin D5
        pin_d5.duty_cycle = int(speed_percent * duty_max) # cast b/c duty cycle must be an integer

            #state_direction = 'forward'

        time.sleep(time_swing) # wait
        #count_loops += 1

        was_pressed = True

        # set motor off
        pin_d5.duty_cycle = 0
    # if button not pressed (whether button was just pressed or not)
    elif button_swing.value == 1:

        was_pressed = False # change previous button state to not pressed if else statement runs
        # else statement will run if button.value = 1 which means it's not pressed currently
        #print(count_loops)
    # else (button pressed and button was just pressed) -- do nothing until button is released and the elif runs to change was_pressed to False



        # NOTES
        # so far, seems like motor starts spinning above 0.54V from the feather,
        # so 0.54/3.3 % of the duty cycle
        # TEST THIS FURTHER to scale the speed percent I send to the motor so I can get the scale as wide as possible
        # (so the bottom quarter of the 'knob' isn't just dead space with an annoying beeping noise)

    print(was_pressed)
    time.sleep(0.01) # wait
