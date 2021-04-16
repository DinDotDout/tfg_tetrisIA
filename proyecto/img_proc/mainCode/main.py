import sys
import argparse
import serial
import numpy as np
import math

import cv2

import FileVideoStream as fvs
import SwitchController as ctrler
import image_processing as img_process

# BUTTONS
up_pad = 'w'
down_pad = 's'
left_pad = 'a'
right_pad = 'd'
a_button = 'l'
b_button = 'k'
l_button = 'j'

# Number of frames to waste
wait_time = 0
# reset frame waste
wait_reset = 20 #1 sec aprox
add_frames = '+'
subtract_frames = '-'
frame_change = 20

auto_state = 1
auto_pilot = False


# KEY MAPPING AND COMMANDS
# map keyboard to controls
# last_k = None
def controller(k):
    # global last_k
    # if auto_pilot:
    #     ctrler.send_cmd()
    # else:
    #     if k != last_k:
    #         ctrler.send_cmd()    
    # if last_k != k:
    #     ctrler.send_cmd()
    if k == up_pad:
        ctrler.send_cmd(ctrler.DPAD_U)

    if k == left_pad:
        ctrler.send_cmd(ctrler.DPAD_L)

    if k == down_pad:
        ctrler.send_cmd(ctrler.DPAD_D)

    if k == right_pad:
        ctrler.send_cmd(ctrler.DPAD_R)

    if k == a_button:
        ctrler.send_cmd(ctrler.BTN_A)

    if k == b_button:
        ctrler.send_cmd(ctrler.BTN_B)

    if k == l_button:
        ctrler.send_cmd(ctrler.BTN_L)

        

    # last_k = k
    # if auto pilot is active actions are delayed


# Resets the frame waste counter
def start_frame_waste():
    global wait_time
    wait_time = wait_reset

# Adds or subtracts number of frames to waste between actions
def adjust_wait_time(command):
    global wait_reset
    if command == add_frames:
        wait_reset = wait_reset + frame_change
        print("Current frame waste:")
        print(wait_reset)
    elif command == subtract_frames:
        wait_reset = wait_reset - frame_change
        print("Current frame waste:")
        print(wait_reset)
    
# Decreases grame counter if it's higher than 0
def waste_frames():
    global wait_time
    if wait_time > 0:
        wait_time = wait_time - 1
    return wait_time


# Auto mode selector
def state_controller():
    global auto_state
    switcher = {
        # 1: screen_selector,
        # 2: screen_selector,
        1: img_process.game_processing,
        2: img_process.game_processing,
        3: img_process.game_processing,
    }
    if not waste_frames():
        func = switcher.get(auto_state, "Invalid state")
        func()

def screen_selector():
    correct_screen = img_process.selection_screen_detection()
    if correct_screen:
        controller(a_button)
        global auto_state
        auto_state = auto_state + 1
        start_frame_waste()
    else:
        controller(right_pad)
        controller(up_pad)
        start_frame_waste()

# Main
# -----------------------------------------------
def main():
    # We get the 2 arguments and process them for its use
    parser = argparse.ArgumentParser('Tetris gaming')
    parser.add_argument('port')
    parser.add_argument(type=int, default= 1,
                        help="Image device selector", dest = 'cap')
    args = parser.parse_args()

    # opencv_version = cv2.__version__
    # print(opencv_version)

    print('Opening serial port')
    # Only first baudrate seems to be able to sync
    ctrler.serialPort = serial.Serial(port=args.port, baudrate=19200, timeout=1)
    # ser = serial.Serial(port=args.port, baudrate=31250,timeout=1)
    # ser = serial.Serial(port=args.port, baudrate=40000,timeout=1)
    # ser = serial.Serial(port=args.port, baudrate=62500,timeout=1)

    # Attempt to sync with the MCU
    print('Synchronizing pc with Nintendo Switch')
    if not ctrler.sync():
        print('Could not sync!')

    print('Sending test packet')
    if not ctrler.send_cmd():
        print('Packet Error!')
        sys.exit()
    print('Packet succesful')
    print('Synchronized')

    # Frame buffer
    width = 1266
    height = 720
    print('Preparing frame buffer...')
    cap = fvs.FileVideoStream(args.cap, width = width, height = height).start()
    print('Frame buffer ready')

    # Name of the window we will use
    winname = 'Nintendo Switch'
    cv2.namedWindow(winname)

    # Set screen to full size
    cv2.setWindowProperty(winname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    global auto_pilot
    last_k = None
    changed = False

    while(cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) >= 1):
        frame = cap.read()
        # read keyboard input
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        elif k == ord('y'):
            auto_pilot = not auto_pilot
        
        # Dont clean last command if pressing the same key
        if k == 255:
            ctrler.send_cmd()
        # Automatic mode
        if auto_pilot:
            img_process.frame = frame
            state_controller()
        # Player controller mode
        else:

            command = chr(k)
            adjust_wait_time(command)
            controller(command)
        
        # show the frame 
        cv2.imshow(winname, frame)
        

    # When everything done, release the capture and controller
    cap.stop()
    cv2.destroyAllWindows()
    ctrler.close

if __name__ == "__main__":
    main()
