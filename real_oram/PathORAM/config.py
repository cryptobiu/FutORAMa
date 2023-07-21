

import math
from real_oram.config import baseConfig


class config(baseConfig):


    def __init__(self, N, is_map=False):
        self.N = N
        self.Z = 4
        self.X = 4
        self.KEY_SIZE = math.ceil(math.ceil(math.log(N,2))/8)
        if not is_map:
            self.BALL_DATA_SIZE = 16
            # the balls structure:  KEY || LEAF || DATA
            self.BALL_SIZE = 2*self.KEY_SIZE + self.BALL_DATA_SIZE
        else:
            self.UPPER_LAYER_KEY_SIZE = math.ceil(math.ceil(math.log(N*self.X,2))/8)
            self.BALL_DATA_SIZE = 2*self.UPPER_LAYER_KEY_SIZE*self.X
            # the balls structure:  KEY || LEAF || [ LEAF' ]*X
            self.BALL_SIZE = 2*self.KEY_SIZE + self.BALL_DATA_SIZE
            # raise "not implemented yet"
        
        self.LOCAL_MEMORY_SIZE = 131_220*16
        self.LOCAL_MEMORY_SIZE_IN_BALLS = int(self.LOCAL_MEMORY_SIZE/self.BALL_SIZE)
        self.DATA_SIZE = N*self.BALL_SIZE*2*self.Z
        self.BUCKET_SIZE = self.Z*self.BALL_SIZE
        self.NUMBER_OF_LEVELS = int(math.ceil(math.log(N,2))) + 1