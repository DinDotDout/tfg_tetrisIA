# import pieceController as pc
import numpy as np
import random as rnd

import board as b
import piece as pc
import tile as t

board = b.Board()
# print(len(board.mainPiece.offset_list))
# for offset in board.mainPiece.offset_list:
#     print(offset)
#     print("eh")
while(True):
    key = input()
    if key == "w":
        board.drop_piece()
    if(key == "a"):
        board.move_piece(np.array([-1,0]))
    if(key == "s"):
        board.move_piece(np.array([0,-1]))
    if(key == "d"):
        board.move_piece(np.array([1,0]))
    if(key == "c"):
        board.rotate_piece(False, True)
    if(key == "v"):
        board.rotate_piece(True, True)
    if(key == "p"):
        break
