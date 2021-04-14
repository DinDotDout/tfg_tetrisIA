import numpy as np
import tile as tc
from abc import abstractmethod

# __all__ = ['ZPiece', 'IPiece', 'OPiece', 'SPiece', 'TPiece', 'JPiece', 'LPiece']

class Piece(object):

    offset_list = np.array(
        [
            [
                [0, 0],
                [0, 0],
                [0, 0],
                [0, 0]
            ],
            [
                [0, 0],
                [1, 0],
                [0, 0],
                [-1, 0]
            ],
            [
                [0, 0],
                [1, -1],
                [0, 0],
                [-1, -1]
            ],
            [
                [0, 0],
                [0, 2],
                [0, 0],
                [0, 2]
            ],
            [
                [0, 0],
                [1, 2],
                [0, 0],
                [-1, 2]
            ]
        ]
    )
    
    def __init__(self):
        self.rotationIndex = 0
        self.tiles = [tc.Tile() for i in range(4)]

    # def __str__(self):
    #     return super().__str__()
    
    @abstractmethod
    def make_shape(self):
        raise NotImplementedError

    #  <summary>
    #  Rotates the piece by 90 degrees in specified direction. Offest operations should almost always be attempted,
    #  unless you are rotating the piece back to its original position.
    #  </summary>
    #  <param name="clockwise">Set to true if rotating clockwise. Set to False if rotating CCW</param>
    #  <param name="shouldOffset">Set to true if offset operations should be attempted.</param>
    # def rotate_Piece(self, clockwise, shouldOffset):
    #     oldRotationIndex = self.rotationIndex

    #     self.rotationIndex += 1 if clockwise else -1
    #     rotationIndex = rotationIndex%4

    #     for i in range(len(self.tiles)):
    #         self.tiles[i].rotate_tile(self.tiles[0].coordinates, clockwise)

    #     if not shouldOffset:
    #         return

    #     canOffset = offset(oldRotationIndex, rotationIndex)

    #     if not canOffset:
    #         rotate_Piece(not clockwise, False)

    def rotate(self, clockwise):
        oldRotationIndex = self.rotationIndex
        self.rotationIndex += 1 if clockwise else -1
        self.rotationIndex %= 4
        for i in range(len(self.tiles)):
            self.tiles[i].rotate_tile(self.tiles[0].position, clockwise)
        
    
    def offset(self, oldRotIndex, newRotIndex):
        offsetVal1 = offsetVal2 = None
        endOffset = np.array([0,0])

        movePossible = False

        for testIndex in range(len(self.offset_list)):
            offsetVal1 = self.offset_list[testIndex, oldRotIndex];
            offsetVal2 = self.offset_list[testIndex, newRotIndex];
            endOffset = offsetVal1 - offsetVal2;
            if (can_move_piece(endOffset)):
                movePossible = True
                break

        if movePossible:
            move_piece(endOffset)
        else:
            print("Move impossible")
        return movePossible

    def can_move_piece(self, endOffset):
        print("eh")
    def move_piece(self, endOffset):
        print("oh")

    @property
    def color(self):
        raise NotImplementedError

    @property
    def tiles(self):
        return self._tiles

    @tiles.setter
    def tiles(self, tiles):
        self._tiles = tiles

    @property
    def rotationIndex(self):
        return self._rotationIndex

    @rotationIndex.setter
    def rotationIndex(self, rotationIndex):
        self._rotationIndex = rotationIndex

class SPiece(Piece):
    color = (0, 255, 0)

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,1])
        self.tiles[3].position = np.array([0,1])

class ZPiece(Piece):
    color = (255, 0, 0)

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([0,1])
        self.tiles[2].position = np.array([-1,1])
        self.tiles[3].position = np.array([1,0])

class IPiece(Piece):
    color = (0, 255, 255)

    offset_list = np.array(
        [
            [
                [0, 0],
                [-1, 0],
                [-1, 1],
                [0, 1]
            ],
            [
                [-1, 0],
                [0, 0],
                [1, 1],
                [0, 1]
            ],
            [
                [2, 0],
                [0, 0],
                [-2, 1],
                [0, 1]
            ],
            [
                [-1, 0],
                [0, 1],
                [1, 0],
                [0, -1]
            ],
            [
                [2, 0],
                [0, -2],
                [-2, 0],
                [0, 2]
            ]
        ]
    )

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,0]) * 2
        self.tiles[3].position = np.array([1,0])

class OPiece(Piece):
    color = (255, 255, 0)
    offset_list = np.array(
        [
            [
                [0, 0],
                [0, -1],
                [-1, -1],
                [-1, 0]
            ]
        ]
    )

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([1,0])
        self.tiles[2].position = np.array([1,1])
        self.tiles[3].position = np.array([0,1])

class LPiece(Piece):
    color = (255, 165, 0)

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([1,1])
        self.tiles[3].position = np.array([1,0])

class JPiece(Piece):
    color = (0, 0, 255)

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([-1,1])
        self.tiles[3].position = np.array([1,0])

class TPiece(Piece):
    color = (128, 0, 128)

    def make_shape(self):
        for tile in self.tiles:
            tile.color = self.color
        self.tiles[1].position = np.array([-1,0])
        self.tiles[2].position = np.array([0,1])
        self.tiles[3].position = np.array([1,0])
