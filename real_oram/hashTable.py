import math
from real_oram.RAM.local_RAM import local_RAM
from collections import defaultdict
from real_oram.utils.byte_operations import ByteOperations
from real_oram.thresholdGenerator import ThresholdGenerator
from real_oram.utils.cuckoo_hash import CuckooHash
from real_oram.utils.helper_functions import get_random_string
from real_oram.utils.oblivious_sort import ObliviousSort
from real_oram.config import config
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
        self.threshold_generator = ThresholdGenerator(conf)
        self.local_stash = {}
        self.mixed_stripe_ram = local_RAM(conf.MIXED_STRIPE_LOCATION, conf)
        self.cuckoo = CuckooHash(conf)
        self.dummy = conf.DUMMY_STATUS*conf.BALL_SIZE
        self.dummy_bin = self.createDummies(conf.BIN_SIZE)
        
        

    def createDummies(self, count):
        return [self.dummy]*count
    
    # This function creates random data for testing.
    def createReadMemory(self):
        current_write = 0
        while current_write < self.conf.DATA_SIZE:
            random_bin = [get_random_string(self.conf.BALL_SIZE, self.conf.BALL_STATUS_POSITION, self.conf.DATA_STATUS) for i in range(self.conf.BIN_SIZE)]
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], random_bin)
            current_write += self.conf.BIN_SIZE_IN_BYTES
        while current_write < 2*self.conf.DATA_SIZE:
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
    
    # This function prepares the bins for writing.
    # It fills the bins with empty values.
    def cleanWriteMemory(self):
        # Cleaning the bins
        current_write = 0
        while current_write < self.conf.DATA_SIZE*2:
            self.bins_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
        
        #Cleaning the overflow pile
        current_write = 0
        FINAL_OVERFLOW_SIZE = 2**math.ceil(math.log(self.conf.OVERFLOW_SIZE + self.conf.LOG_LAMBDA*self.conf.NUMBER_OF_BINS,2))
        while current_write < FINAL_OVERFLOW_SIZE*2:
            self.overflow_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            self.second_overflow_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
    
    def emptyData(self):
        current_write = 0
        while current_write < 2*self.conf.DATA_SIZE:
            self.data_ram.writeChunks(
                [(current_write, current_write + self.conf.BIN_SIZE_IN_BYTES)], self.createDummies(self.conf.BIN_SIZE))
            current_write += self.conf.BIN_SIZE_IN_BYTES
        

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
                self.randCyclicShift(int(offset), start_loc, ram)
            self._tightCompaction(start_loc, ram, int(offset), dummy_statuses)
            
            offset /= 2
            distance_from_center /=2
            iteration += 1
    
    def randCyclicShift(self, NUMBER_OF_BINS, start_loc, ram: local_RAM):
        if NUMBER_OF_BINS == 1:
            return
        if NUMBER_OF_BINS <= 2*self.conf.MU:
            current_read = start_loc
            while current_read <= start_loc + NUMBER_OF_BINS*self.conf.BIN_SIZE_IN_BYTES:
                number_of_shifts = int(2*self.conf.MU/NUMBER_OF_BINS)
                balls = ram.readChunk((current_read, current_read + number_of_shifts*NUMBER_OF_BINS*self.conf.BALL_SIZE))
                shift_amounts = [random.randint(0, NUMBER_OF_BINS) for _ in range(number_of_shifts)]
                shifted_balls = []
                start_index = 0
                for i in range(number_of_shifts):
                    shift_amount = shift_amounts[i]
                    end_index = start_index + NUMBER_OF_BINS
                    section = balls[start_index:end_index]
                    shifted_section = section[shift_amount:] + section[:shift_amount]
                    shifted_balls.extend(shifted_section)
                    start_index = end_index
                
                ram.writeChunk((current_read, current_read + number_of_shifts*NUMBER_OF_BINS*self.conf.BALL_SIZE),shifted_balls)
                current_read += number_of_shifts*NUMBER_OF_BINS*self.conf.BALL_SIZE
        else:
            raise NotImplementedError('this is not implemented yet.')
                
                
        
    
    def _tightCompaction(self, start_loc, ram, offset, dummy_statuses):
        for i in range(offset):
            balls = self.byte_operations.readTransposed(ram, offset, start_loc + i*self.conf.BALL_SIZE, 2*self.conf.MU)
            balls = self.localTightCompaction(balls, dummy_statuses)
            self.byte_operations.writeTransposed(ram, balls, offset, start_loc + i*self.conf.BALL_SIZE)
        
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
        self.threshold_generator.reset()
        current_bin = 0
        iteration_num = 0
        while current_bin < self.conf.NUMBER_OF_BINS:
            # Step 1: read how much each bin is full
            # we can read 1/EPSILON bins at a time since from each bin we read 2*EPSILON*MU balls
            capacity_chunks = [(i*self.conf.BIN_SIZE_IN_BYTES,i*self.conf.BIN_SIZE_IN_BYTES + self.conf.BALL_SIZE) for i in range(current_bin, current_bin + int(1/self.conf.EPSILON))]
            bins_capacity = self.bins_ram.readChunks(capacity_chunks)
            # bins_capacity is a list of int, each int indicates how many balls in the bin
            bins_capacity = [int.from_bytes(bin_capacity, 'big', signed=False) for bin_capacity in bins_capacity]
            
            #Step 2: read the 2*MU*EPSILON top balls from each bin
            chunks = []
            for index,capacity in enumerate(bins_capacity):
                bin_num = index + current_bin
                end_of_bin = bin_num*self.conf.BIN_SIZE_IN_BYTES + self.conf.BALL_SIZE*(capacity+1)
                end_of_bin_minus_epsilon = end_of_bin - int(2*self.conf.MU*self.conf.EPSILON*self.conf.BALL_SIZE)
                chunks.append((end_of_bin_minus_epsilon,end_of_bin))
            balls = self.bins_ram.readChunks(chunks)
            # bin_tops is a list of lists of balls, each list of balls is the top 2*MU*EPSILON from it's bin
            bin_tops = [balls[x:x+int(2*self.conf.MU*self.conf.EPSILON)] for x in range(0, len(balls), int(2*self.conf.MU*self.conf.EPSILON))]
            
            # Step 3: select the secret load and write it to the overflow pile (also update the capacities)
            capacity_threshold_balls = self._moveSecretLoad(bins_capacity, bin_tops, iteration_num, chunks)
            iteration_num += 1
            current_bin += int(1/self.conf.EPSILON)
            
            self.bins_ram.writeChunks(capacity_chunks[:len(capacity_threshold_balls)], capacity_threshold_balls)

    def _moveSecretLoad(self, bins_capacity, bin_tops, iteration_num, write_to_bins_chunks):
        write_balls = []
        write_back_balls = []
        i = 0
        capacity_threshold_balls = []
        for capacity,bin_top in zip(bins_capacity,bin_tops):
            
            # This is to skip the non-existant bins.
            # Example: 32 bins, epsilon = 1/9.
            # so we pass on 9 bins at a time, but in the last iteration we pass on the last five bins and then we break.
            if iteration_num*(1/self.conf.EPSILON) + i >= self.conf.NUMBER_OF_BINS:
                break
            
            # generate a threshold
            threshold = self.threshold_generator.generate()
            while threshold >= capacity:
                raise Exception("Error, threshold is greater than capacity")
                
            # Add only the balls above the threshold
            write_balls.extend(bin_top[- (capacity - threshold):])
            i +=1
            
            # write back only the balls beneath the threshold
            write_back = bin_top[:- (capacity - threshold)]
            write_back.extend(self.createDummies(len(bin_top) - len(write_back)))
            write_back_balls.extend(write_back)
            
            
            capacity_threshold_balls.append(self.byte_operations.constructCapacityThresholdBall(capacity, threshold))
        
        # Add the appropriate amount of dummies
        write_balls.extend(self.createDummies(2*self.conf.MU - len(write_balls)))
        
        # Write to the overflow transposed (for the tight compaction later)
        self.byte_operations.writeTransposed(self.overflow_ram, write_balls, self.conf.NUMBER_OF_BINS_IN_OVERFLOW, iteration_num*self.conf.BALL_SIZE)
        
        # Write back to the bins
        self.bins_ram.writeChunks(write_to_bins_chunks[:i], write_back_balls)
        
        return capacity_threshold_balls

    def ballsIntoBins(self):
        current_read_pos = 0
        balls = []
        
        # in the final table to save space, the rams switch.
        if self.conf.FINAL:
            self.data_ram, self.bins_ram = self.bins_ram, self.data_ram
        
        while current_read_pos < self.bins_ram.getSize():
            balls = self.data_ram.readChunks(
                [(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)])
            
            
            self._ballsIntoBins(balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
        
        
        self.conf.reset()
        
            
            

    def _ballsIntoBins(self, balls):
        local_bins_dict = defaultdict(list)
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DUMMY_STATUS:
                local_bins_dict[int(random.randint(0,self.conf.NUMBER_OF_BINS-1))].append(self.dummy)
            else:
                local_bins_dict[self.byte_operations.ballToPseudoRandomNumber(ball, self.conf.NUMBER_OF_BINS)].append(ball)
        
        start_locations = [bin_num * self.conf.BIN_SIZE_IN_BYTES for bin_num in local_bins_dict.keys()]
        bins_capacity = zip(local_bins_dict.keys(), self.bins_ram.readBalls(start_locations))
        
        write_chunks = []
        write_balls = []
        for bin_num, capacity_ball in bins_capacity:
            capacity = self.byte_operations.getCapacity(capacity_ball)
            if capacity >= 2*self.conf.MU -1:
                raise Exception("Error, bin is too full")
            bin_loc = bin_num*self.conf.BIN_SIZE_IN_BYTES
            bin_write_loc = bin_loc + (capacity + 1) * self.conf.BALL_SIZE
            new_balls = local_bins_dict[bin_num]

            # updating the capacity
            new_capacity_ball = (capacity + len(new_balls)).to_bytes(self.conf.BALL_SIZE, 'big')
            write_chunks.append((bin_loc, bin_loc + self.conf.BALL_SIZE))
            write_balls.append(new_capacity_ball)

            # balls into bin
            write_chunks.append((bin_write_loc, bin_write_loc + len(new_balls) * self.conf.BALL_SIZE))
            write_balls.extend(new_balls)
        self.bins_ram.writeChunks(write_chunks,write_balls)

    def cuckooHashBins(self):
        current_bin_index = 0
        overflow_written = 0
        stashes = []
        while current_bin_index < self.conf.NUMBER_OF_BINS:
            
            # get the bin
            bin_data = self.bins_ram.readChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )])
            capacity, threshold = self.byte_operations.deconstructCapacityThresholdBall(bin_data[0])
            bin_data = bin_data[1:threshold+1]
            
            # generate the cuckoo hash
            cuckoo_hash = CuckooHash(self.conf)
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.bins_ram.writeChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            self.addToLocalStash(cuckoo_hash.stash)
            current_bin_index += 1
        

        
    def obliviousBallsIntoBins(self):
        if self.conf.NUMBER_OF_BINS_IN_OVERFLOW <= 1:
            return
        oblivious_sort = ObliviousSort(self.conf)
        self._obliviousBallsIntoBinsFirstIteration(oblivious_sort)
        next_ram = self.overflow_ram
        current_ram = self.second_overflow_ram
        for bit_num in range(1,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2))):
            first_bin_index = 0
            for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
                first_bin = current_ram.readChunks([(first_bin_index*self.conf.BIN_SIZE_IN_BYTES, (first_bin_index + 1)*self.conf.BIN_SIZE_IN_BYTES)])
                second_bin = current_ram.readChunks([
                    ((first_bin_index + 2**bit_num)*self.conf.BIN_SIZE_IN_BYTES, (first_bin_index + (2**bit_num) + 1)*self.conf.BIN_SIZE_IN_BYTES)])
                bin_zero, bin_one = oblivious_sort.splitToBinsByBit(first_bin + second_bin,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2)) - 1 - bit_num, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
                
                next_ram.writeChunks(
                    [(bin_index*2*self.conf.BIN_SIZE_IN_BYTES, (bin_index +1)*2*self.conf.BIN_SIZE_IN_BYTES)], bin_zero + bin_one)
                first_bin_index +=1
                if first_bin_index % 2**bit_num == 0:
                    first_bin_index += 2**bit_num
            next_ram, current_ram = current_ram, next_ram
        self.overflow_ram = current_ram
        self.second_overflow_ram = next_ram
    
    def _obliviousBallsIntoBinsFirstIteration(self,oblivious_sort):
        current_read_pos = 0
        for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
            balls = self.overflow_ram.readChunks([(current_read_pos, current_read_pos + self.conf.BIN_SIZE_IN_BYTES)])
            bin_zero, bin_one = oblivious_sort.splitToBinsByBit(balls, math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2))-1, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
            self.second_overflow_ram.writeChunks(
                [(2*current_read_pos, 2*current_read_pos + 2*self.conf.BIN_SIZE_IN_BYTES)], bin_zero + bin_one)
            current_read_pos += self.conf.BIN_SIZE_IN_BYTES
        
    def cuckooHashOverflow(self):
        current_bin_index = 0
        while current_bin_index < self.conf.NUMBER_OF_BINS_IN_OVERFLOW:
            # get the bin
            bin_data = self.overflow_ram.readChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )])

            # generate the cuckoo hash
            cuckoo_hash = CuckooHash(self.conf)
            cuckoo_hash.insert_bulk(bin_data)

            # write the data
            hash_tables = cuckoo_hash.table1 + cuckoo_hash.table2
            self.overflow_ram.writeChunks([(current_bin_index*self.conf.BIN_SIZE_IN_BYTES, (current_bin_index +1)*self.conf.BIN_SIZE_IN_BYTES )],hash_tables)
            
            # write the stash
            self.addToLocalStash(cuckoo_hash.stash)
            current_bin_index += 1
    
    def addToLocalStash(self, balls):
        for ball in balls:
            self.local_stash[ball[self.conf.BALL_STATUS_POSITION+1:]] = ball
       
    def lookup(self, key):
        # look in local stash
        result_ball = self.createDummies(1)[0]
        ball = self.local_stash.get(key)
        if ball != None:
            result_ball = ball
            self.local_stash[key] = self.byte_operations.changeBallStatus(self.local_stash[key], self.conf.SECOND_DUMMY_STATUS)
            self.reals_count -= 1
        
        table1_location, table2_location = self.cuckoo.get_possible_addresses(key)
        
        # look in overflow
        bin_num = self.byte_operations.keyToPseudoRandomNumber(key, self.conf.NUMBER_OF_BINS_IN_OVERFLOW)
        replacement_ball = self.createDummies(1)[0]
        
        # read
        ball_1,ball_2 = self.overflow_ram.readBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location,self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)]) 
        ball_1_write = ''
        ball_2_write = ''
        # table 1
        if ball_1[self.conf.BALL_STATUS_POSITION+1:] == key and ball_1[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DATA_STATUS:
            result_ball = ball_1
            ball_1_write = ball_1[:self.conf.BALL_STATUS_POSITION] + self.conf.SECOND_DUMMY_STATUS + random.randint(2**27,2**28).to_bytes(self.conf.KEY_SIZE,'big')
            self.reals_count -= 1
        else:
            ball_1_write = ball_1
        
        # table 2
        if ball_2[self.conf.BALL_STATUS_POSITION+1:] == key and ball_2[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1]== self.conf.DATA_STATUS:
            result_ball = ball_2
            ### RANDOM KEY NOT SAME KEY
            ball_2_write = ball_2[:self.conf.BALL_STATUS_POSITION] + self.conf.SECOND_DUMMY_STATUS + random.randint(2**27,2**28).to_bytes(self.conf.KEY_SIZE,'big')
            self.reals_count -= 1
        else:
            ball_2_write = ball_2
        
        self.overflow_ram.writeBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location, self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)], [ball_1_write, ball_2_write])

        # if the ball was found with a standard data status, then continue with dummy lookups
        if result_ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DATA_STATUS:
            key = get_random_string(self.conf.BALL_SIZE - self.conf.BALL_STATUS_POSITION -1)
        
        # look in bins
        bin_num = self.byte_operations.keyToPseudoRandomNumber(key, self.conf.NUMBER_OF_BINS)
        
        ball_1,ball_2 = self.bins_ram.readBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location, self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)]) 


        # table 1
        if ball_1[self.conf.BALL_STATUS_POSITION+1:] == key and ball_1[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DATA_STATUS:
            result_ball = ball_1
            ball_1_write = ball_1[:self.conf.BALL_STATUS_POSITION] + self.conf.SECOND_DUMMY_STATUS + random.randint(2**27,2**28).to_bytes(self.conf.KEY_SIZE,'big')
            self.reals_count -= 1
        else:
            ball_1_write = ball_1
        
        # table 2
        if ball_2[self.conf.BALL_STATUS_POSITION+1:] == key and ball_2[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] == self.conf.DATA_STATUS:
            result_ball = ball_2
            ball_2_write = ball_2[:self.conf.BALL_STATUS_POSITION] + self.conf.SECOND_DUMMY_STATUS + random.randint(2**27,2**28).to_bytes(self.conf.KEY_SIZE,'big')
            self.reals_count -= 1
        else:
            ball_2_write = ball_2
        self.bins_ram.writeBalls([self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*table1_location, self.conf.BIN_SIZE_IN_BYTES*bin_num + self.conf.BALL_SIZE*(self.conf.MU + table2_location)], [ball_1_write, ball_2_write])

        return result_ball

    # this function copies the previous layer into the current layer for intersperse
    def copyToEndOfBins(self, second_data_ram:local_RAM, reals):
        current_read_pos = 0
        self.reals_count += reals
        while current_read_pos < self.conf.DATA_SIZE:
            balls = second_data_ram.readChunks(
                [(current_read_pos, current_read_pos + self.conf.LOCAL_MEMORY_SIZE)])
            self.bins_ram.writeChunks(
                [(self.conf.DATA_SIZE + current_read_pos, self.conf.DATA_SIZE + current_read_pos + self.conf.LOCAL_MEMORY_SIZE)], balls)
            current_read_pos += self.conf.LOCAL_MEMORY_SIZE
    
    
    # THIS NEEDS TO BE CHECKED
    def extract(self):
        5+ 5
        self.obliviousBallsIntoBinsExtract()
        balls_written = 0
        stash = list(self.local_stash.values())
        
        for i in range(self.conf.NUMBER_OF_BINS_IN_OVERFLOW):
            # read the overflow
            overflow_bin = self.overflow_ram.readChunk((i*self.conf.BIN_SIZE_IN_BYTES,(i+1)*self.conf.BIN_SIZE_IN_BYTES))
            for j in range(int(1/self.conf.EPSILON)):
                # read the bin to extract
                bin = self.bins_ram.readChunk(((i*int(1/self.conf.EPSILON)+j)*self.conf.BIN_SIZE_IN_BYTES,(i*int(1/self.conf.EPSILON)+j+1)*self.conf.BIN_SIZE_IN_BYTES))
                for ball in overflow_bin + stash:
                    if self.byte_operations.ballToPseudoRandomNumber(ball, self.conf.NUMBER_OF_BINS) == i*int(1/self.conf.EPSILON)+j:
                        bin.append(ball)
                bin = [ball for ball in bin if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION + 1] != self.conf.DUMMY_STATUS]
                self.bins_ram.writeChunk((balls_written*self.conf.BALL_SIZE, balls_written*self.conf.BALL_SIZE + len(bin)*self.conf.BALL_SIZE), bin)
                balls_written += len(bin)
        
        
    
    def obliviousBallsIntoBinsExtract(self):
        if self.conf.NUMBER_OF_BINS_IN_OVERFLOW <= 1:
            bin = self.overflow_ram.readChunk((0,self.conf.BIN_SIZE_IN_BYTES))
            bin = self.localTightCompaction(bin,[self.conf.DUMMY_STATUS])
            self.overflow_ram.writeChunk((0,self.conf.BIN_SIZE_IN_BYTES), bin)
            return
        oblivious_sort = ObliviousSort(self.conf)
        # self._obliviousBallsIntoBinsFirstIteration(oblivious_sort)
        current_ram = self.overflow_ram
        next_ram = self.second_overflow_ram
        for bit_num in range(0,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2))):
            first_bin_index = 0
            for bin_index in range(math.ceil(self.conf.NUMBER_OF_BINS_IN_OVERFLOW/2)):
                first_bin = current_ram.readChunks([(first_bin_index*self.conf.BIN_SIZE_IN_BYTES, (first_bin_index + 1)*self.conf.BIN_SIZE_IN_BYTES)])
                second_bin = current_ram.readChunks([
                    ((first_bin_index + 2**bit_num)*self.conf.BIN_SIZE_IN_BYTES, (first_bin_index + (2**bit_num) + 1)*self.conf.BIN_SIZE_IN_BYTES)])
                bin_zero, bin_one = oblivious_sort.splitToBinsByBitExtract(first_bin + second_bin,math.ceil(math.log(self.conf.NUMBER_OF_BINS_IN_OVERFLOW,2)) - 1 - bit_num, self.conf.NUMBER_OF_BINS, self.conf.EPSILON)
                
                next_ram.writeChunks(
                    [(bin_index*2*self.conf.BIN_SIZE_IN_BYTES, (bin_index +1)*2*self.conf.BIN_SIZE_IN_BYTES)], bin_zero + bin_one)
                first_bin_index +=1
                if first_bin_index % 2**bit_num == 0:
                    first_bin_index += 2**bit_num
            next_ram, current_ram = current_ram, next_ram
        self.overflow_ram = current_ram
        self.second_overflow_ram = next_ram
    
# self.markAuxiliary(self.conf.N, 2*self.conf.N)
# self.binsTightCompaction([self.conf.SECOND_DATA_STATUS, self.conf.SECOND_DUMMY_STATUS])
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
            balls = self.byte_operations.readTransposed(ram, offset, start_loc + i*self.conf.BALL_SIZE, 2*self.conf.MU)
            random.shuffle(balls)
            self.byte_operations.writeTransposed(ram, balls, offset, start_loc + i*self.conf.BALL_SIZE)
    