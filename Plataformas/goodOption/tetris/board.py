import numpy as np
import random as rnd
import tile as tc
import piece as pc

class Board():

    def __init__(self):

        self.gridSizeY = 20
        self.gridSizeX = 10
        self.grid = self.create_grid()

        self.bag = [] # list off upcoming pieces
        self.fill_bag()

        self.piecePos = np.array([0,0])
        self.mainPiece = self.spawn_piece()
        # print(self)
        
        
    # Creates a grid of sized based off of gridSizeX and gridSizeY variables
    def create_grid(self):
        grid = [[0 for col in range(self.gridSizeX)] for row in range(self.gridSizeY)]
        for y in range(self.gridSizeY):
            for x in range(self.gridSizeX):
                grid[y][x] = GridCell()
        return grid

    def __str__(self):
        out = []
        for row in self.grid:
            out.append(''.join([str(cell) for cell in row]))

        mainBlocks = []
        if self.mainPiece:
            for tiles in self.mainPiece.tiles:
                x, y = tiles.position+self.piecePos
                if y < 20:
                    replacement = out[y][:x] + '1' + out[y][x+1:]
                    out[y] = replacement
        out.reverse()
        return '\n'.join(out)

    def spawn_piece(self):
        pieces = {
            0: pc.IPiece(),
            1: pc.JPiece(),
            2: pc.LPiece(),
            3: pc.OPiece(),
            4: pc.SPiece(),
            5: pc.TPiece(),
            6: pc.ZPiece()
        }
        # Append next bag if current bag is under 7
        if len(self.bag) < 7:  # check to see if list is empty
            self.fill_bag()

        current_piece = pieces.get(self.bag.pop(0), pc.Piece())  # get current piece
        current_piece.make_shape()
        self.piecePos = np.array([4,21])
        return current_piece
    
    def fill_bag(self):
        piecesToAdd = [0, 1, 2, 3, 4, 5, 6]  # refill list
        rnd.shuffle(piecesToAdd)  # shuffle list
        self.bag.extend(piecesToAdd)  # add new pieces

    def rotate_piece(self, clockwise, shouldOffset):
        oldRotation = self.mainPiece.rotationIndex
        self.mainPiece.rotate(clockwise)
        newRotation = self.mainPiece.rotationIndex

        movePossible = True
        if shouldOffset:
            movePossible = self.offset_piece(oldRotation, newRotation)
        if not movePossible:
            self.mainPiece.rotate(not clockwise)
        
    def offset_piece(self,oldRotation, newRotation):
        for offset in self.mainPiece.offset_list:
            offsetVal1 = offset[oldRotation]
            offsetVal2 = offset[newRotation]
            endOffset = offsetVal1 - offsetVal2
            if (self.move_piece(endOffset, True)):
                return True
        return False

    # Checks if all tiles can be moved to the position and does so
    def move_piece(self, movement, isOffseting = False):
        canMove = True
        for tile in self.mainPiece.tiles:
            globalTilePos = self.piecePos + tile.position # center position + tile displacement
            newGlobalTilePos = globalTilePos + movement # add movement
            if not self.is_in_bounds(newGlobalTilePos) or not self.is_cell_empty(newGlobalTilePos):
                canMove = False
                break

        if not canMove:
            if movement[0] == 0 and movement[1] == -1 and not isOffseting: # Lock piece if cant move down
                self.lock_piece()
            return False 
        self.piecePos += movement
        # print(self)
        return True

    def global_piece_positions(self):
        positions = []
        for tile in self.mainPiece.tiles:
            globalTilePos = self.piecePos + tile.position
            positions.append(globalTilePos)
        return positions

    def lock_piece(self):
        for tile in self.mainPiece.tiles:
            globalTilePos = self.piecePos + tile.position
            x, y = globalTilePos
            self.grid[y][x].isOccupied = True
            self.grid[y][x].block = tile
        self.check_line_clears()
        self.mainPiece = self.spawn_piece()
        
    def drop_piece(self):
        canDrop = True
        down = np.array([0,-1])
        while canDrop:
            canDrop = self.move_piece(down)

    # Checks to see if the coordinate is within the tetris board bounds
    def is_in_bounds(self, pos):
        x, y = pos
        if x < 0 or x >= self.gridSizeX or y < 0:
            return False
        else:
            return True

    # Checks to see if the coordinates are occupied by a block
    def is_cell_empty(self, pos):
        x, y = pos
        if y >= self.gridSizeY:
            return True
        if self.grid[y][x].isOccupied:
            return False
        else:
            return True

    def clear_line(self, line):
        if line < 0 or line > self.gridSizeY:
            print("line out of bounds")
            return
        
        for x in range(self.gridSizeX):
            self.grid[line][x].block = None
            self.grid[line][x].isOccupied = False
            # curBlock = self.grid[line][x].block
            # # curBlock.tiles[grid[line][x].block.tileIndex] = None # Delete tile itself
            # # clearLine!!!
            # # Destroy(fullGrid[x, lineToClear].tileOnGridUnit)

            # if not curBlock.AnyTilesLeft():
            #     # Also clear block
            #     # Destroy(curBlock.gameObject)
            #     self.grid[line][x].block = None
            #     self.grid[line][lixne].isOccupied = False
    
    def check_line_clears(self):
        linesToClear = []
        consecutiveLineClears = 0

        for y in range(self.gridSizeY):
            lineClear = True
            for x in range(self.gridSizeX):
                if not self.grid[y][x].isOccupied:
                    lineClear = False
                    consecutiveLineClears = 0
                
            if lineClear:
                linesToClear.append(y)
                consecutiveLineClears += 1
                if consecutiveLineClears == 4:
                    # print TETRIS! and add points
                    print("TETRIS!")
                
                self.clear_line(y)

        # //Once the lines have been cleared, the lines above those will drop to fill in the empty space
        if len(linesToClear) > 0:
            for i in range(len(linesToClear)):
            
                # /* The initial index of lineToDrop is calculated by taking the index of the first line
                #  * that was cleared then adding 1 to indicate the index of the line above the cleared line,
                #  * then the value i is subtracted to compensate for any lines already cleared.
                #  */
                for lineToDrop in range(linesToClear[i] + 1 - i, self.gridSizeY):
                    for x in range(self.gridSizeX):
                        cell = self.grid[lineToDrop][x]     
                        if cell.isOccupied and lineToDrop < 20:

                            self.grid[lineToDrop][x].block = cell.block
                            self.grid[lineToDrop][x].isOccupied = True
                            cell.block = None
                            cell.isOccupied = False

                            # self.move_tile_down(cell)

    def move_tile_down(self, cell):
        block = cell.block
        block.move_tile(np.array([0, -1])) # Move down
        block.set_tile()
        cell.block = None
        cell.isOccupied = False

    def grid_colors(self):
        gridColors = [[0 for col in range(self.gridSizeX)] for row in range(self.gridSizeY)]
        tilePositions = self.global_piece_positions()
        for y in range(0, self.gridSizeY):
            for x in range(0, self.gridSizeX):
                block = self.grid[y][x].block
                color = block.color if block else (0, 0, 0)
                gridColors[y][x] = color

        for pos in tilePositions:
            x, y = pos
            if y < 20:
                gridColors[y][x] = self.mainPiece.color
        gridColors.reverse()
        return gridColors


    # def piece_removed(self, pieceCoords):
    #     for coords in pieceCoords:
    #         cell =self.grid[coords.x, coords.y]
    #         cell.tileOnGridUnit = None
    #         cell.isOccupied = False
        

    #     for i in range(len(pieceCoords)):
    #         for y in range(pieceCoords[i].y + 1,self.gridSizeY):
    #             cell =self.grid[pieceCoords[i].x, y]
    #             if cell.isOccupied:
    #                 move_tile_down(cell)
                  
    #     check_line_clears()           
                
                   

class GridCell:
    def __init__(self):
        # self.location = vector(x,y)
        self.isOccupied = False
        self.block = None

    def __str__(self):
        return str(1 if self.isOccupied else 0)