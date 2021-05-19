import sys
import argparse
import serial
import numpy as np
import math
import time

import cv2

from . import fileVideoStream as fvs
from . import switchController as ctrler
from . import image_processing as img_process
from neural_net import heuristic_calc as hc, run_net as net
from tetris_game.tetrisStructure import board


# BUTTONS
up_pad = 'w'
down_pad = 's'
left_pad = 'a'
right_pad = 'd'
a_button = 'l' # rotate right
b_button = 'k' # rotate left
l_button = 'j' # swap piece

# Number of frames to waste
wait_time = 0
timeMark = 0

add_frames = '+'
subtract_frames = '-'
frame_change = 20

auto_state = 1


# KEY MAPPING AND COMMANDS
# map keyboard to controls
# last_k = None
def controller(k):
    
    if k == left_pad:
        ctrler.send_cmd(ctrler.DPAD_L)
    elif k == up_pad:
        ctrler.send_cmd(ctrler.DPAD_U)
    elif k == down_pad:
        ctrler.send_cmd(ctrler.DPAD_D)

    elif k == right_pad:
        ctrler.send_cmd(ctrler.DPAD_R)

    elif k == a_button:
        ctrler.send_cmd(ctrler.BTN_A)

    elif k == b_button:
        ctrler.send_cmd(ctrler.BTN_B)

    elif k == l_button:
        ctrler.send_cmd(ctrler.BTN_L)


    # last_k = k
    # if auto pilot is active actions are delayed


def start_time_counter():
    global timeMark
    timeMark = time.perf_counter()

def check_wait_timer(waitTime):
    global timeMark
    currTime = time.perf_counter()

    if currTime - timeMark < waitTime:
        return False
    else:
        return True

# Resets the frame waste counter
def start_frame_waste(wait_reset):
    global wait_time
    wait_time = wait_reset

# # Adds or subtracts number of frames to waste between actions
# def adjust_wait_time(command):
#     # global wait_reset
#     if command == add_frames:
#         wait_reset = wait_reset + frame_change
#         print("Current frame waste:")
#         print(wait_reset)
#     elif command == subtract_frames:
#         wait_reset = wait_reset - frame_change
#         print("Current frame waste:")
#         print(wait_reset)
    
# Decreases frame counter if it's higher than 0
def waste_frames():
    global wait_time
    if wait_time > 0:
        wait_time = wait_time - 1
    return wait_time

def screen_selector():
    correct_screen = img_process.selection_screen_detection()
    if correct_screen:
        controller(a_button)
        global auto_state
        auto_state = auto_state + 1
        start_frame_waste(20)
    else:
        controller(right_pad)
        controller(up_pad)
        start_frame_waste(20)


# Auto mode selector
def state_controller(k):
    global auto_state
    switcher = {
        # 1: screen_selector,
        # 2: screen_selector,
        1: img_process.game_processing,
        2: img_process.game_processing,
        3: img_process.game_processing,
    }
    func = switcher.get(auto_state, "Invalid state")
    # print('\n'.join([''.join(['{:4}'.format(item) for item in row]) 
    #     for row in img_process.game_matrix]))
    # print("")
    func()
    img_process.game_processing()

moves = []
lastCPUMove = False
clean = False

expectedPos = None
piece = None
def run_net(frame):
    global moves, clean, expectedPos, piece

    if img_process.canMove and not moves:
        displacement, rotation, expectedPos, piece = net.get_net_output(img_process.gameBoard)
        # print(type(piece))
        moves = queue_moves(displacement, rotation)
        # moves.extend()
        # print(moves)

    if piece:
        draw_expected_pos(expectedPos, piece, frame)

    timer = 0.04
    # timer = 0.5
    if check_wait_timer(timer):
        if clean:
            # print("clean")
            ctrler.send_cmd()
            clean = False
            start_time_counter()
            # print()
        elif moves:
            move = moves.pop()
            # print(move)

            # print(move)
            controller(move)
            start_time_counter()
            clean = True
        else:
            img_process.canMove = True
            piece = None


def draw_expected_pos(expectedPos, piece, frame):
    pixel_x = 496
    pixel_y = 56
    box_spacing = 32
    for tile in  piece.tiles:
        x, y = expectedPos + tile.position
        cv2.putText(frame, "POS", (pixel_x+(x*box_spacing), pixel_y+((19-y)*box_spacing)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (piece.color[2], piece.color[1], piece.color[0]))
    # print(expectedPos)
    # print(expectedPos[0])
    # print(19-expectedPos)
    # print(env)
    # print()


def queue_moves(displacement, rotation):
    "Return a queue with the movements to perform"
    moves = []

    # Piece swap
    if displacement == 6:
        moves.append(l_button)
        # print("swap")
        return moves

    # Drop piece
    moves.append(up_pad)
    
    # Place in correct column
    if displacement > 0:
        for i in range(displacement):
            moves.append(right_pad)
    elif displacement < 0:
        for i in range(abs(displacement)):
            moves.append(left_pad)
    
    # Rotate piece
    for i in range(rotation):
        moves.append(a_button)

    return moves

# Main
# -----------------------------------------------
def main():
    global moves, lastCPUMove, clean, expectedPos, piece

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
    if not ctrler.serialPort:
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

    print("Loading neual net data")
    net.load_net()

    # Name of the window we will use
    winname = 'Nintendo Switch'
    cv2.namedWindow(winname)

    # Set screen to full size
    cv2.setWindowProperty(winname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    auto_pilot = False

    lastCommand = 255
    frame = None
    while(cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) >= 1):
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        elif k == ord('y'):
            moves = []
            lastCPUMove = False
            clean = False

            expectedPos = None
            piece = None
            auto_pilot = not auto_pilot

        if cap.has_frame():
            frame = cap.read()
            if auto_pilot:
                img_process.frame = frame
                img_process.game_processing()
        # read keyboard input

        
        # Dont clean last command if pressing the same key
        # if k == 255 and not auto_pilot:
        #     ctrler.send_cmd()
        # Automatic mode
        if auto_pilot:
            run_net(frame)
            # img_process.game_processing()
        # Player controller mode
        else:

            if k != 255:
                command = chr(k)
                controller(command)
                
                start_time_counter()
                lastCommand = k
            else:
                if check_wait_timer(0.1) and lastCommand != 255:
                    ctrler.send_cmd()
                    lastCommand = 255
            # if k == 255:
            #     ctrler.send_cmd()
            # if check_wait_timer(0.1):
            #     command = chr(k)
            #     # adjust_wait_time(command)
            #     controller(command)
            #     start_time_counter()
            # elif :
            #     ctrler.send_cmd()
        
        # show the frame 
        cv2.imshow(winname, frame)
        

    # When everything done, release the capture and controller
    cap.stop()
    cv2.destroyAllWindows()
    ctrler.close

# if __name__ == "__main__":
#     main()
