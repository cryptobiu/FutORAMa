from real_oram.PathORAM.config import config
import random

class CruchORAM:
    def __init__(self, number_of_blocks) -> None:
        self.number_of_blocks = number_of_blocks
        self.conf = config(number_of_blocks)
        self.dic = {}

    def position_map_access(self, key):
        old_leaf = random.randint(0,self.number_of_blocks*self.conf.X-1) if key not in self.dic else self.dic[key]
        self.dic[key] = random.randint(0,self.number_of_blocks*self.conf.X-1)
        return old_leaf, self.dic[key]
