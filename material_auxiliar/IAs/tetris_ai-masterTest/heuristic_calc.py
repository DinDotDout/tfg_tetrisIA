import random
import numpy as np
from time import sleep
import copy

import tetris_game.tetrisStructure.piece as piece
from tetris_game import tetris as tetris

    
def get_next_states(board):
    '''Get all possible next states'''
    # states = {}

    displacementsL = list(reversed(range(-5, 0)))
    displacementsR = list(range(0, 6))

    rotations = 4
    if type(board.mainPiece) is piece.OPiece: # O piece is in the same position even if we rotate
        rotations = 1
    elif type(board.mainPiece) is piece.SPiece or type(board.mainPiece) is piece.ZPiece or type(board.mainPiece) is piece.IPiece:
        rotations = 2
    gridStates = list()
    nextPiecesStates = list()
    moves = list()
    scores = list()
    dones = list()

    initialBoard = copy.deepcopy(board) # Save initial board state
    gamePiece = copy.deepcopy(board.mainPiece) # We will use this piece to preserve rotation
    
    is_include_hold = False
    is_new_hold = False

    if board.canStore and type(board.storedPiece) != type(board.mainPiece):  # Add store move to dictionary
        is_include_hold = True
        is_new_hold = not board.storedPiece
        move = [6,0]

        board.swap_piece()
        landingHeight = board.piecePos[1]

        gridState, nextPiecesState, score = get_board_props(board)
        gridStates.append(gridState)
        nextPiecesStates.append(nextPiecesState)

        # moves += [move]
        # scores += [score]
        moves.append(move)
        scores.append(score)
        dones.append(board.gameOver)

        grid = [x[:] for x in initialBoard.grid] # reset board game
        bag = [x for x in initialBoard.bag] # reset board bag
        
        board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
            mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece),
            canStore = initialBoard.canStore, score= initialBoard.score)

    for rotation in range(rotations): # For all rotations

        testMovements(displacementsL, rotation, board, initialBoard, gamePiece, gridStates, nextPiecesStates, moves, scores, dones) # test left movents
        testMovements(displacementsR, rotation, board, initialBoard, gamePiece, gridStates, nextPiecesStates, moves, scores, dones) # test right movents

        movePosible = board.rotate_piece(False, True) # rotates piece left for the next iteration
        gamePiece = copy.deepcopy(board.mainPiece) # replace gamePiece with new rotation

        # Get out of loop if cannot rotate piece anymore
        if not movePosible:
            break


    board = copy.deepcopy(initialBoard)
    return [np.concatenate(gridStates), np.concatenate(nextPiecesStates)], np.array([scores]).reshape(
            [len(scores), 1]), dones, is_include_hold, is_new_hold, moves, board

def testMovements(displacements, rotation, board, initialBoard, gamePiece, gridStates, nextPiecesStates, moves, scores, dones):
    for displacement in displacements: # try all displacement
        isValid = True # No movement is also valid

        if displacement > 0: # move right
            isValid = board.move_piece(np.array([1,0]))
        elif displacement < 0: # move left
            isValid = board.move_piece(np.array([-1,0]))


        # store current position
        piecePos = copy.deepcopy(board.piecePos)
        if isValid: 

            # tile local positions
            tiles = [i.position[1] for i in board.mainPiece.tiles] # check tile local position before piece changes (drop)

            # Drop piece to bottom and get pos height, and lines cleared
            landingHeight = board.drop_piece()

            gridState, nextPiecesState, score = get_board_props(board)
            gridStates.append(gridState)
            nextPiecesStates.append(nextPiecesState)       

            scores.append(score)
            moves.append([displacement, rotation])
            dones.append(board.gameOver)
 
            # Reset board but keep piece horizontal displacement
            grid = [x[:] for x in initialBoard.grid] # reset board game
            bag = [x for x in initialBoard.bag] # reset board bag
            board.reset(grid = grid, bag = bag, piecePos = piecePos,
                mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece), 
                canStore = initialBoard.canStore, score= initialBoard.score)
        else:
            # cannot keep moving in direction
            break
        
    # Reset board and position at the end
    grid = [x[:] for x in initialBoard.grid] # reset board game
    bag = [x for x in initialBoard.bag] # reset board bag
    board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
        mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece), 
        canStore = initialBoard.canStore, score= initialBoard.score)

def play(board, displacement, rotation, isExploration = False):
    '''Makes a play given a position and a rotation, returning the reward and if the game is over'''
    # initialScore = board.score
    lastPos = board.piecePos
    if displacement == 6:
        board.swap_piece()
        # tetris.draw(board)
    else:
        displacement = displacement*np.array([1, 0])
        
        for i in range(rotation):
            # tetris.draw(board)
            board.rotate_piece(False)

        # Move piece to column
        board.move_piece(displacement)
        # tetris.draw(board)

        # Drop piece
        lastPos = board.drop_piece(isExploration)
        lines = board._check_line_clears()
        # tetris.draw(board)

    return board.gameOver, lastPos

def get_reward(scores, dones):
    reward = list()
    # manipulate the reward
    for i in range(len(scores)):
        score = scores[i].item()
        if dones[i]:
            score += 500 # penalty
        reward.append(score)
    return np.array(reward).reshape([-1, 1])

def get_board_props(board):
    lines = len(board._check_line_clears())

    gameGrid = get_grid(board)
    next_pieces = get_upcoming_and_stored_pieces(board)
    score = (lines + 1) * lines / 2 * 10
    # if board.gameOver:
    #     score = -500
    
    return gameGrid, next_pieces, score
    
def get_upcoming_and_stored_pieces(board):
        # part1: heights + hold_depth. len -> 20
    buffer1 = [_total_height(board)] + [sum(get_hole_depth(board))]
    # part2: current 1; hold 1; next 4
    # next will always be the last for convenience, because of the change in the last one
    # hold has one more position to record if last step is 'hold'
    hold_num = 1
    current_num = 1

    # Modify to use all 6
    next_num = 4

    # Number of piece types
    pool_size = 7
    buffer2 = [0] * (pool_size * (hold_num + current_num + next_num) + hold_num)

    if hold_num == 1:
        if not board.canStore:
            buffer2[0] = 1
        if board.storedPiece != None:
            storedPieceType = piece.get_piece_number(board.storedPiece)
            buffer2[storedPieceType + hold_num] = 1

    mainPieceType = piece.get_piece_number(board.mainPiece)
    buffer2[hold_num + hold_num * pool_size + mainPieceType] = 1

    for i in range(next_num):
        mainPieceType = board.bag[i]
        buffer2[hold_num + (i + hold_num + current_num) * pool_size + mainPieceType] = 1
    return np.reshape(np.array(buffer1 + buffer2, dtype='int8'), [1, -1])

# Hightes buried hole
def get_hole_depth(board):
    depth = [0] * board.gridSizeX
    highest_brick = 0
    for j in range(board.gridSizeX):
        has_found_brick = False
        board.grid[j]
        for i in reversed(range(board.killHeight - 1)):
            if not has_found_brick:
                if board.grid[i][j] != None:
                    has_found_brick = True
                    highest_brick = i 
            elif board.grid[i][j] == None:
                depth[j] = highest_brick - i 
                break
    return depth

def _total_height(board):
    '''Sum and maximum height of the board'''
    sum_height = 0

    for x in range(board.gridSizeX):
        height = 0
        for y in reversed(range(board.killHeight - 1)):
            if board.grid[y][x]:
                height = y+1 # 0 row will be counted as height 1
                break
        sum_height += height
    return sum_height

# Get grid state
def get_grid(board):
    buffer = []
    for i in reversed(range(board.killHeight-1)):
        for j in range(board.gridSizeX):
            buffer.append([board.grid[i][j] != None] )

    buffer = np.reshape(np.array(buffer), [1, board.killHeight-1, board.gridSizeX, 1])

    return buffer



