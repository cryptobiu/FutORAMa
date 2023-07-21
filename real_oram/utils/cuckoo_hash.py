from real_oram.config import config
import random
from real_oram.utils.byte_operations import ByteOperations

class CuckooHash:
    def createDummies(self, count):
        return [self.dummy]*count
    
    def __init__(self, conf:config) -> None:
        self.conf = conf
        self.dummy = conf.DUMMY_STATUS*conf.BALL_SIZE
        self.table1_byte_operations = ByteOperations(self.conf.CUCKOO_HASH_KEY_1, conf)
        self.table2_byte_operations = ByteOperations(self.conf.CUCKOO_HASH_KEY_2, conf)
        self.table1 = self.createDummies(self.conf.MU)
        self.table2 = self.createDummies(self.conf.MU)
        self.stash = []

    # Level one has no overflow-pile which raises the stash-size as it fills half the spaces.
    # But it's ok because it's bounded by MU and therefore would not blow-up the local memory
    def insert_bulk(self, balls):
        random.shuffle(balls)
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                continue
            self.insert_ball(ball)
    
    def insert_ball(self, ball):
        seen_locations = []
        while True:
            location = self.table1_byte_operations.ballToPseudoRandomNumber(ball,self.conf.MU)
            evicted_ball = self.table1[location]
            self.table1[location] = ball
            if evicted_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                break
            ball = evicted_ball
            location = self.table2_byte_operations.ballToPseudoRandomNumber(ball,self.conf.MU)
            evicted_ball = self.table2[location]
            self.table2[location] = ball
            if evicted_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                break
            ball = evicted_ball
            if len(seen_locations) > 2*self.conf.MU:
                if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] != self.conf.DUMMY_STATUS:
                    self.stash.append(ball)
                break
            seen_locations.append(location)
            
    def get_possible_addresses(self, key):
        table1_location = self.table1_byte_operations.keyToPseudoRandomNumber(key, self.conf.MU)
        table2_location = self.table2_byte_operations.keyToPseudoRandomNumber(key, self.conf.MU)
        return table1_location, table2_location