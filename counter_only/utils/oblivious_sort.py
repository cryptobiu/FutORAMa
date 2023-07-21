from counter_only.config import config
from counter_only.utils.byte_operations import ByteOperations


class ObliviousSort:
    def __init__(self, conf:config) -> None:
        self.conf = conf
        self.byte_operations = ByteOperations(self.conf.MAIN_KEY, conf)
        self.dummy = self.conf.DUMMY_STATUS*self.conf.BALL_SIZE

    def splitToBinsByBit(self, balls, bit_num, number_of_bins):
        bin_zero = []
        bin_one = []
        for ball in balls:
            if ball == self.dummy:
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
        

