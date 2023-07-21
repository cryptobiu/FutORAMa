from real_oram.config import config
from real_oram.utils.byte_operations import ByteOperations


class ObliviousSort:
    def __init__(self, conf:config) -> None:
        self.conf = conf
        self.byte_operations = ByteOperations(self.conf.MAIN_KEY, conf)
        self.dummy = self.conf.DUMMY_STATUS*self.conf.BALL_SIZE

    def splitToBinsByBit(self, balls, bit_num, number_of_bins):
        bin_zero = []
        bin_one = []
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                continue
            assigned_bin = self.byte_operations.ballToPseudoRandomNumber(ball, number_of_bins)
            bit = self.byte_operations.isBitOn(assigned_bin, bit_num)
            if bit:
                bin_one.append(ball)
            else:
                bin_zero.append(ball)
        # bin_one = bin_one + [self.dummy] * (self.conf.BIN_SIZE - len(bin_one))
        # bin_zero = bin_zero + [self.dummy] * (self.conf.BIN_SIZE - len(bin_zero))
        bin_one.extend([self.dummy] * (self.conf.BIN_SIZE - len(bin_one)))
        bin_zero.extend([self.dummy] * (self.conf.BIN_SIZE - len(bin_zero)))
        return bin_zero, bin_one
    
    def splitToBinsByBitExtract(self, balls, bit_num, number_of_bins, epsilon):
        bin_zero = []
        bin_one = []
        for ball in balls:
            if ball[self.conf.BALL_STATUS_POSITION: self.conf.BALL_STATUS_POSITION+1] == self.conf.DUMMY_STATUS:
                continue
            assigned_bin = self.byte_operations.ballToPseudoRandomNumber(ball, number_of_bins)
            assigned_bin = int(assigned_bin*epsilon)
            bit = self.byte_operations.isBitOn(assigned_bin, bit_num)
            if bit:
                bin_one.append(ball)
            else:
                bin_zero.append(ball)
        # bin_one = bin_one + [self.dummy] * (self.conf.BIN_SIZE - len(bin_one))
        # bin_zero = bin_zero + [self.dummy] * (self.conf.BIN_SIZE - len(bin_zero))
        bin_one.extend([self.dummy] * (self.conf.BIN_SIZE - len(bin_one)))
        bin_zero.extend([self.dummy] * (self.conf.BIN_SIZE - len(bin_zero)))
        return bin_zero, bin_one
        

