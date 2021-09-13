import sys
import argparse
import serial
import numpy as np
import math
import time
import copy

import cv2

from . import fileVideoStream as fvs
from . import switch_controller as ctrler
from . import image_processing as img_process
from neural_net import heuristic_calc as hc, ai_manager as net
from tetris_game.tetrisStructure import board
from tetris_game.tetrisStructure import piece

np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 

# BUTTONS
# Arrow keys
up_pad = 38
down_pad = 40
left_pad = 37
right_pad = 39

up_stick = ord("i")
down_stick = ord("k")
left_stick = ord("j")
right_stick = ord("l")

a_button = ord("d") # rotate right
b_button = ord("a") # rotate left
l_button = ord(" ") # swap piece
pause_button = ord("p")

# Flow control
exit = 27 # Esc
activate_net = 13 # Intro

# up_pad = ord("i")
# down_pad = ord("l")
# left_pad = ord("j")
# right_pad = ord("k")


wait_time = 0 # Time to waste
timeMark = 0 # Time mark to start counting

auto_state = 1
def controller(k):
    '''Sends according command to the controller for the switch to receive'''
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
    elif k == pause_button:
        ctrler.send_cmd(ctrler.BTN_PLUS)
    elif k == up_stick:
        ctrler.send_cmd(ctrler.LSTICK_U)
    elif k == down_stick:
        ctrler.send_cmd(ctrler.LSTICK_D)
    elif k == left_stick:
        ctrler.send_cmd(ctrler.LSTICK_L)
    elif k == right_stick:
        ctrler.send_cmd(ctrler.LSTICK_R)


def start_time_counter():
    '''Stpres a time mark as reference for a time counter'''
    global timeMark
    timeMark = time.perf_counter()

def check_wait_timer(waitTime):
    '''Returns if the selected time has passe since the counter was started'''
    global timeMark
    currTime = time.perf_counter()

    if currTime - timeMark < waitTime:
        return False
    else:
        return True


moves = []
bag = []
storedPiece = None
clean = False
expectedPos = None
piece = None
lines = 0
env = None
def flow_manager(frame):
    '''Asks neural net for output whenever it is deemed necessary'''
    global moves, clean, expectedPos, piece, bag, storedPiece, env
    if img_process.gameBoard and (not np.array_equal(img_process.gameBoard.bag[:3], bag) or 
        type(storedPiece) != type(img_process.gameBoard.storedPiece)) and not moves:
        ask_net_img()
        # ask_net_predict()

    # If there is and expected piece to be placed, draw it
    if piece:
        draw_expected_pos(expectedPos, piece, frame)

    next_move_timer = 0.027

    # Checks to see if time has passeds
    if check_wait_timer(next_move_timer):
        if clean: # clean last input if enough time has passed
            ctrler.send_cmd()
            clean = False
            start_time_counter()
            if not moves: # last move just executed
                piece = None
        elif moves: # send new move
            move = moves.pop()
            # if move == up_pad# Stop dropping the piece at high levels
            controller(move)
            controller(move)
            start_time_counter()
            clean = True

            

# def _grid_deviations(grid1, grid2):
#     deviations = 0
#     for x, y in zip(grid1[:20], grid2[:20]):
#         for x1, y1 in zip(x, y):
#             if x1 and not y1 or not x1 and y1:
#                 deviations += 1
#     return deviations

def ask_net_img():
    '''Asks the neural net for moves and stores them'''
    global moves, bag, storedPiece, piece, expectedPos, lines, env
    bag = img_process.gameBoard.bag[:3] # we will use it to avoid executing same sequence more than once
    storedPiece = img_process.gameBoard.storedPiece    

    # If can draw and last moves where cleared
    displacement, rotation, expectedPos, piece, points, env = net.get_net_output(img_process.gameBoard)
    moves = queue_moves(displacement, rotation)
    lines += points

def ask_net_predict():
    '''Asks the neural net for moves and stores them'''
    global moves, bag, storedPiece, piece, expectedPos, lines, env
    if not env:
        env = copy.deepcopy(img_process.gameBoard)

    env.bag = copy.deepcopy(img_process.gameBoard.bag)
    env.storedPiece = copy.deepcopy(img_process.gameBoard.storedPiece)
    bag = img_process.gameBoard.bag[:3] # we will use it to avoid executing same sequence more than once
    storedPiece = img_process.gameBoard.storedPiece    
    
    # If can draw and last moves where cleared
    displacement, rotation, expectedPos, piece, points, env = net.get_net_output(env)
    moves = queue_moves(displacement, rotation)
    lines += points 

def draw_expected_pos(expectedPos, piece, frame):
    '''Draws a piece that we want directly on the game grid'''
    pixel_x = 496
    pixel_y = 56
    box_spacing = 32
    for tile in  piece.tiles:
        x, y = expectedPos + tile.position
        cv2.putText(frame, "POS", (pixel_x+(x*box_spacing), pixel_y+((19-y)*box_spacing)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (piece.color[2], piece.color[1], piece.color[0]))


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
        moves.append(b_button)

    return moves

# Main
# -----------------------------------------------
def main():
    global moves, bag, clean, expectedPos, piece, lines, env

    # We get the 2 arguments and process them for its use
    parser = argparse.ArgumentParser('Tetris gaming')
    parser.add_argument( help="COM port selector", dest = 'port')
    # parser.add_argument(type=int, default= 1,
    #                     help="Image device selector", dest = 'cap')
    args = parser.parse_args()
    
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
        return
    print('Packet succesful')
    print('Synchronized')

    # Frame buffer
    width = 1266
    height = 720
    print('Preparing frame buffer...')
    cap = fvs.FileVideoStream(width = width, height = height).start() # Input from capture card
    print('Frame buffer ready')

    print("Loading neural net data")
    found = net.load_model()
    if not found:
        return

    # Name of the window we will use
    winname = 'Nintendo Switch'
    cv2.namedWindow(winname)

    # Set screen to full size
    cv2.setWindowProperty(winname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    auto_pilot = False
    lastCommand = -1
    frame = None
    while(cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) >= 1):
        # k = cv2.waitKey(1)
        k = cv2.waitKeyEx(1) # Special keys active

        if k == exit: # Esc key
            break
        elif k == activate_net: # clean up autoplay info
            img_process.gameBoard = None 
            moves = []
            bag = []
            env = None
            lines = 0
            nextPiece = None
            storedPiece = None
            clean = False

            expectedPos = None
            piece = None
            auto_pilot = not auto_pilot

        if cap.has_frame():
            frame = cap.read()
            if auto_pilot: # Only process frame when there is a new one
                img_process.frame = frame # Send frame info to game processing
                img_process.game_processing() # Image detection on frame
        
        
        if auto_pilot: # Automatic mode
            flow_manager(frame)
        else: # Player controller mode
            # read keyboard input
            if k != -1: # If command received
                # command = chr(k)
                controller(k) # send command to switch
                start_time_counter()
                lastCommand = k
            else:
                if check_wait_timer(0.06) and lastCommand != -1: # Send command cleanup to switch after a some time
                    ctrler.send_cmd()
                    lastCommand = -1
        # show the frame 
        cv2.imshow(winname, frame)
        

    # When everything done, release the capture and controller
    cap.stop()
    cv2.destroyAllWindows()
    ctrler.close
