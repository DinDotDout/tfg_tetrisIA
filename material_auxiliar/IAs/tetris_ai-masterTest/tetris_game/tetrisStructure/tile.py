import numpy as np
class Tile(object):

    def __init__(self):
        self.color = (0, 0, 0)
        self.position = np.array([0,0])

    def rotate_tile(self, originPos, clockwise):
        relativePos = self.position - originPos
        rotMatrix = np.array([[0,-1],[1,0]]) if clockwise else np.array([[0,1],[-1,0]])
        newXPos = (rotMatrix[0][0] * relativePos[0]) + (rotMatrix[1][0] * relativePos[1])
        newYPos = (rotMatrix[0][1] * relativePos[0]) + (rotMatrix[1][1] * relativePos[1])
        newPos = np.array([newXPos, newYPos])
        newPos += originPos
        self.position = newPos
    

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
    
    def __str__(self):
        return "color: %s, position: %s" % (self.color, self.position)