import random
import numpy as np
from time import sleep
import copy

from tetris_game.tetrisStructure import piece as piece
from tetris_game import tetris as tetris

penalty = -500

def get_next_states(board):
    '''Get all possible next states and returns board as it was'''

    # Max eft and right displacements allowed
    displacementsL = list(reversed(range(-5, 0)))
    displacementsR = list(range(0, 6))

    # Max rotations allowed
    rotations = 4

    if type(board.mainPiece) is piece.OPiece:
        rotations = 1 # O piece is in the same position even if we rotate
    elif type(board.mainPiece) is piece.SPiece or type(board.mainPiece) is piece.ZPiece or type(board.mainPiece) is piece.IPiece:
        rotations = 2 # S, Z and I 3rd and 4th rotations are almost equal to 1st and 2nd

    gridStates = list() # Possible future grid states
    nextPiecesStates = list() # Board Props + possible upcoming pieces + held piece
    moves = list() # Possible moves
    scores = list() # Future scores
    dones = list() # Envs finished

    initialBoard = copy.deepcopy(board) # Save initial board state
    gamePiece = copy.deepcopy(board.mainPiece) # We will use this piece to preserve rotation
    
    is_include_hold = False # Could hold piece
    is_new_hold = False # New held piece

    if board.canStore and type(board.storedPiece) != type(board.mainPiece):  # Add store move if should
        is_include_hold = True
        is_new_hold = not board.storedPiece
        move = [6,0] # This impossible move is percieved as a hold move later on

        board.swap_piece() # Perform the hold moce

        # Store all info
        gridState, nextPiecesState, score = get_board_props(board)
        gridStates.append(gridState)
        nextPiecesStates.append(nextPiecesState)
        moves.append(move)
        scores.append(score)
        dones.append(board.gameOver)

        # Reset board state
        grid = [x[:] for x in initialBoard.grid] # reset board game
        bag = [x for x in initialBoard.bag] # reset board bag
        
        board.reset(grid = grid, bag = bag, piecePos = copy.deepcopy(initialBoard.piecePos),
            mainPiece = copy.deepcopy(gamePiece), storedPiece = copy.deepcopy(initialBoard.storedPiece),
            canStore = initialBoard.canStore, score= initialBoard.score)

    for rotation in range(rotations): # For all rotations
        # Try left and right movements
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
    '''Try all displacements given a rotation and store them'''
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
            board.drop_piece()

            # Store all info
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
    '''Makes a play given a position and a rotation, returning  game is over'''
    rotatedPiece = None
    lastPos = board.piecePos
    lines = []
    if displacement == 6:
        board.swap_piece()
    else:
        displacement = displacement*np.array([1, 0])
        
        for i in range(rotation):
            board.rotate_piece(False)

        # Move piece to column
        board.move_piece(displacement)

        rotatedPiece = copy.deepcopy(board.mainPiece)
        
        # Drops piece
        lastPos = board.drop_piece(isExploration)
        lines = board._check_line_clears()
    return lastPos, rotatedPiece, len(lines)

def get_reward(add_scores, dones):
    '''Adds an according penalty to lost games'''
    reward = list()
    # manipulate the reward
    for i in range(len(add_scores)):
        add_score = add_scores[i].item()
        if dones[i]:
            add_score += penalty
        reward.append(add_score)
    return np.array(reward).reshape([-1, 1])

def get_board_props(board):
    '''Calculates wanted board metrics'''
    lines = len(board._check_line_clears()) # Line clears
    gameGrid = get_grid(board) # Board state
    next_pieces = get_props_and_pieces(board) # Board helping metrics
    score = (lines + 1) * lines / 2 * 10 # Score formula for line clears
    # if board.gameOver:
    #     score = -500
    
    return gameGrid, next_pieces, score
    
def get_props_and_pieces(board):
    '''Board helping metrics'''
    # heights + hole_depth

    buffer1 = [_total_height(board)] + [sum(get_hole_depth(board))]
    # current piece; held piece; next 4 pieces

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
        if mainPieceType != 7: # if piece is None don't add info
            buffer2[hold_num + (i + hold_num + current_num) * pool_size + mainPieceType] = 1
    return np.reshape(np.array(buffer1 + buffer2, dtype='int8'), [1, -1])

def get_hole_depth(board):
    '''Hightes buried hole depth'''
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
    '''Total height of the board'''
    sum_height = 0

    for x in range(board.gridSizeX):
        height = 0
        for y in reversed(range(board.killHeight - 1)):
            if board.grid[y][x]:
                height = y+1 # 0 row will be counted as height 1
                break
        sum_height += height
    return sum_height

def get_grid(board):
    '''Game grid state as a bool matrix'''
    buffer = []
    for i in reversed(range(board.killHeight-1)):
        for j in range(board.gridSizeX):
            buffer.append([board.grid[i][j] != None] )

    buffer = np.reshape(np.array(buffer), [1, board.killHeight-1, board.gridSizeX, 1])

    return buffer
