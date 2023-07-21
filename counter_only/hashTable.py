import math
from counter_only.RAM.local_RAM import local_RAM
from collections import defaultdict
from counter_only.utils.byte_operations import ByteOperations
from counter_only.utils.cuckoo_hash import CuckooHash
from counter_only.utils.helper_functions import get_random_string
from counter_only.utils.oblivious_sort import ObliviousSort
from counter_only.config import config
from operator import itemgetter
import random

class HashTable:

    def __init__(self, conf:config) -> None:
        self.is_built = False
        self.conf = conf
        self.byte_operations = ByteOperations(conf.MAIN_KEY,conf)
        self.data_ram = local_RAM(conf.DATA_LOCATION, conf)
        self.bins_ram = local_RAM(conf.BINS_LOCATION, conf)
        self.overflow_ram = local_RAM(conf.OVERFLOW_LOCATION, conf)
        self.second_overflow_ram = local_RAM(conf.OVERFLOW_SECOND_LOCATION, conf)
        self.local_stash = {}
        self.mixed_stripe_ram = local_RAM(conf.MIXED_STRIPE_LOCATION, conf)
        self.cuckoo = CuckooHash(conf)
        self.dummy = conf.DUMMY_STATUS*conf.BALL_SIZE  

    def rebuild(self, reals):
        self.reals_count = reals
        self.local_stash = {}
        self.ballsIntoBins()
        self.moveSecretLoad()
        self.tightCompaction(self.conf.NUMBER_OF_BINS_IN_OVERFLOW, self.overflow_ram)
        self.cuckooHashBins()
        self.obliviousBallsIntoBins()
        self.cuckooHashOverflow()
        self.is_built = True
        
    def binsTightCompaction(self, dummy_statuses = None):
        self.tightCompaction(self.conf.NUMBER_OF_BINS, self.bins_ram, dummy_statuses)
        
    def tightCompaction(self, NUMBER_OF_BINS, ram, dummy_statuses = None):
        if dummy_statuses == None:
            dummy_statuses = [self.conf.DUMMY_STATUS]
        offset = NUMBER_OF_BINS
        distance_from_center = 1
        midLocation = int(self.conf.EPSILON*self.conf.N)*self.conf.BALL_SIZE
        iteration = 1
        while offset >= 1:
            start_loc = int(midLocation - midLocation*distance_from_center)
            if iteration >= self.conf.RAND_CYCLIC_SHIFT_ITERATION: 
                self._tightCompaction(start_loc, ram, int(offset), dummy_statuses, True)
            else:
                self._tightCompaction(start_loc, ram, int(offset), dummy_statuses)
            
            offset /= 2
            distance_from_center /=2
            iteration +=1
    
    def _tightCompaction(self, start_loc, ram, offset, dummy_statuses, rand_cyclic_shift=False):
        for i in range(offset):
            local_RAM.BALL_READ += 2*self.conf.MU
            local_RAM.RT_READ += 1
            local_RAM.BALL_WRITE += 2*self.conf.MU
            local_RAM.RT_WRITE += 1
            
            ######### additions for randCyclicShift
            # for every bin I need to copy it to a different location and then copy back:
            if rand_cyclic_shift:
                local_RAM.BALL_READ += 2*self.conf.MU
                local_RAM.RT_READ += 2
                local_RAM.BALL_WRITE += 2*self.conf.MU
                local_RAM.RT_WRITE += 2
        
    def localTightCompaction(self, balls, dummy_statuses):
        dummies = []
        result = []
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1 ] in dummy_statuses:
                dummies.append(ball)
            else:
                result.append(ball)
        result.extend(dummies)
        return result
    
    def moveSecretLoad(self):
        current_bin = 0
        iteration_num = 0
        while current_bin < self.conf.NUMBER_OF_BINS:
            # Step 1: read how much each bin is full
            # we can read 1/EPSILON bins at a time since from each bin we read 2*EPSILON*MU balls
            local_RAM.RT_READ += 1
            
            #Step 2: read the 2*MU*EPSILON top balls from each bin
            local_RAM.RT_READ += 1
            local_RAM.BALL_READ += 2*self.conf.MU
            
            # Step 3: select the secret load and write it to the overflow pile (also update the capacities)
            capacity_threshold_balls = self._moveSecretLoad(0, 0, iteration_num, 0)
            iteration_num += 1
            current_bin += int(1/self.conf.EPSILON)
            
            local_RAM.BALL_WRITE += int(1/self.conf.EPSILON)
            local_RAM.RT_WRITE += 1

    def _moveSecretLoad(self, bins_capacity, bin_tops, iteration_num, write_to_bins_chunks):
        capacity_threshold_balls = []
        local_RAM.RT_WRITE += 1
        local_RAM.BALL_WRITE += 2*self.conf.MU
        local_RAM.RT_WRITE += 1
        local_RAM.BALL_WRITE += 2*self.conf.MU
        return capacity_threshold_balls

    def ballsIntoBins(self):
        current_read_pos = 0
        balls = []
        
        # in the final table to save space, the rams switch.
        if self.conf.FINAL:
            self.data_ram, self.bins_ram = self.bins_ram, self.data_ram
        
        while current_read_pos < self.bins_ram.getSize():
            balls = []
            local_RAM.BALL_READ += int(self.conf.LOCAL_MEMORY_SIZE/self.conf.BALL_SIZE)
            local_RAM.RT_READ += 1
            self._ballsIntoBins(balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
        self.conf.reset()

    def _ballsIntoBins(self, balls):
        local_RAM.RT_READ += 1

    def cuckooHashBins(self):
        current_bin_index = 0
        while current_bin_index < self.conf.NUMBER_OF_BINS:
            
            local_RAM.BALL_READ += self.conf.BIN_SIZE
            local_RAM.RT_READ += 1
            local_RAM.BALL_WRITE += self.conf.BIN_SIZE
            local_RAM.RT_WRITE += 1
            current_bin_index += 1
        
        
    def obliviousBallsIntoBins(self):
        oblivious_sort = ObliviousSort(self.conf)
        self._obliviousBallsIntoBinsFirstIteration(oblivious_sort)
        next_ram = self.overflow_ram
        current_ram = self.second_overflow_ram
        for bit_num in range(1,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2))):
            first_bin_index = 0
            for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
                local_RAM.BALL_READ += 2*self.conf.BIN_SIZE
                local_RAM.RT_READ += 1 

                local_RAM.BALL_WRITE += 2*self.conf.BIN_SIZE
                local_RAM.RT_WRITE += 1 
                first_bin_index +=1
                if first_bin_index % 2**bit_num == 0:
                    first_bin_index += 2**bit_num
            next_ram, current_ram = current_ram, next_ram
        self.overflow_ram = current_ram
        self.second_overflow_ram = next_ram
    
    def _obliviousBallsIntoBinsFirstIteration(self,oblivious_sort):
        current_read_pos = 0
        for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
            local_RAM.BALL_READ += self.conf.BIN_SIZE
            local_RAM.RT_READ += 1
            local_RAM.BALL_WRITE += self.conf.BIN_SIZE*2
            local_RAM.RT_WRITE += 1
            current_read_pos += self.conf.BIN_SIZE_IN_BYTES
        
    def cuckooHashOverflow(self):
        current_bin_index = 0
        while current_bin_index < self.conf.NUMBER_OF_BINS_IN_OVERFLOW:
            # get the bin
            local_RAM.BALL_READ += self.conf.BIN_SIZE
            local_RAM.RT_READ += 1 
            # generate the cuckoo hash

            # write the data
            local_RAM.BALL_WRITE += self.conf.BIN_SIZE
            local_RAM.RT_WRITE += 1 
            # write the stash
            current_bin_index += 1
    
    def addToLocalStash(self, balls):
        for ball in balls:
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = ball
       
    def lookup(self, key):
        print('no need to implement in count-only because the tests counts the cost of a lookup')
        # no need to implement in count-only because the tests counts the cost of a lookup

    # this function copies the previous layer into the current layer for intersperse
    def copyToEndOfBins(self, second_data_ram:local_RAM, reals):
        current_read_pos = 0
        self.reals_count += reals
        while current_read_pos < self.conf.DATA_SIZE:
            local_RAM.BALL_READ += int(self.conf.LOCAL_MEMORY_SIZE/self.conf.BALL_SIZE)
            local_RAM.RT_READ += 1
            local_RAM.BALL_WRITE += int(self.conf.LOCAL_MEMORY_SIZE/self.conf.BALL_SIZE)
            local_RAM.RT_WRITE += 1
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
    
    
    
    def extract(self):
        self.obliviousBallsIntoBins()
        for i in range(self.conf.NUMBER_OF_BINS_IN_OVERFLOW):
            # read an overflow bin
            local_RAM.BALL_READ += self.conf.BIN_SIZE
            local_RAM.RT_READ += 1
            for i in range(math.ceil(1/self.conf.EPSILON)):
                # extract 1/epsilon major bins
                local_RAM.BALL_READ += self.conf.BIN_SIZE
                local_RAM.RT_READ += 1
                local_RAM.BALL_WRITE += self.conf.MU
                local_RAM.RT_WRITE += 1
        
    
    def intersperse(self):
        # Alternate intersperse:
        offset = self.conf.NUMBER_OF_BINS
        distance_from_center = 1
        midLocation = int(self.conf.EPSILON*self.conf.N)*self.conf.BALL_SIZE
        while offset >= 1:
            offset /= 2
            distance_from_center /=2
        
        while offset <= self.conf.NUMBER_OF_BINS:
            start_loc = int(midLocation - midLocation*distance_from_center)
            self._intersperse(start_loc, self.bins_ram, int(offset))
            
            offset *= 2
            distance_from_center *=2
    
    def _intersperse(self, start_loc, ram, offset):
        for i in range(offset):
            local_RAM.BALL_READ += 2*self.conf.MU
            local_RAM.RT_READ += 1
            local_RAM.BALL_WRITE += 2*self.conf.MU
            local_RAM.RT_WRITE += 1