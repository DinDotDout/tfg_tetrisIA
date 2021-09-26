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


timeMark = 0 # Time mark to start counting


def controller2(k):
    '''Sends according command to the controller for the switch to receive'''
    if k == left_pad:
        ctrler.write_str("a#")
    elif k == up_pad:
        ctrler.write_str("w#")
    elif k == down_pad:
        ctrler.write_str("s#")
    elif k == right_pad:
        ctrler.write_str("d#")
    elif k == a_button:
        ctrler.write_str("4#")
    elif k == b_button:
        ctrler.write_str("3#")
    elif k == l_button:
        ctrler.write_str("1#")
    elif k == pause_button:
        ctrler.write_str("2#")

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


bag = []
storedPiece = None
expectedPos = None
piece = None
lines = 0
env = None

def flow_manager(frame):
    '''Asks neural net for output whenever it is deemed necessary'''
    global expectedPos, piece, bag, storedPiece, env
    if img_process.gameBoard and (not np.array_equal(img_process.gameBoard.bag[:3], bag) or 
        type(storedPiece) != type(img_process.gameBoard.storedPiece)):
        ask_net_img()
        # ask_net_predict()
        
    # If there is and expected piece to be placed, draw it
    if piece:
        draw_expected_pos(expectedPos, piece, frame)


def ask_net_img():
    '''Asks the neural net for moves and stores them'''
    global bag, storedPiece, piece, expectedPos, lines, env
    bag = img_process.gameBoard.bag[:3] # we will use it to avoid executing same sequence more than once
    storedPiece = img_process.gameBoard.storedPiece    

    # If can draw and last moves where cleared
    displacement, rotation, expectedPos, piece, points, env = net.get_net_output(img_process.gameBoard)
    queue_moves(displacement, rotation)

def ask_net_predict():
    '''Asks the neural net for moves and stores them'''
    global bag, storedPiece, piece, expectedPos, lines, env
    # if not env or img_process.allMatch == True:
        # print("allMatch")
    if not env:
        env = copy.deepcopy(img_process.gameBoard)
    # else:
        # print("no     Match")
    env.bag = copy.deepcopy(img_process.gameBoard.bag)
    env.storedPiece = copy.deepcopy(img_process.gameBoard.storedPiece)

    bag = img_process.gameBoard.bag[:3] # we will use it to avoid executing same sequence more than once
    storedPiece = img_process.gameBoard.storedPiece
    
    # If can draw and last moves where cleared
    displacement, rotation, expectedPos, piece, points, env = net.get_net_output(env)
    queue_moves(displacement, rotation)


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
    moves = ""

    # Piece swap
    if displacement == 6:
        moves += "1#"
        ctrler.write_str(moves)
        return

    # Rotate piece
    for i in range(rotation):
        moves+= "3"

    # Place in correct column
    if displacement > 0:
        for i in range(displacement):
            moves+= "d"
    elif displacement < 0:
        for i in range(abs(displacement)):
            moves+= "a"

    # Drop piece
    moves+= "w"
    
    moves+= "#"

    ctrler.write_str(moves)


# Main
# -----------------------------------------------
def main():
    global bag, expectedPos, piece, lines, env

    # We get the 2 arguments and process them for its use
    parser = argparse.ArgumentParser('Tetris gaming')
    parser.add_argument( help="COM port selector", dest = 'port')
    # parser.add_argument(type=int, default= 1,
    #                     help="Image device selector", dest = 'cap')
    args = parser.parse_args()
    
    print('Opening serial port')
    # Only first baudrate seems to be able to sync
    if not ctrler.serialPort:
        ctrler.serialPort = serial.Serial(port=args.port, baudrate=115200) # robot

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
        
        if k != -1:
            controller2(k) # Player controller mode
        if auto_pilot: # Automatic mode
            flow_manager(frame)
                      
        # show the frame 
        cv2.imshow(winname, frame)
        

    # When everything done, release the capture and controller
    cap.stop()
    cv2.destroyAllWindows()
    ctrler.close
