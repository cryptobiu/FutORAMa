
from real_oram.ORAM import ORAM
from real_oram.RAM.local_RAM import local_RAM, reset_counters
from loading_bar import update_loading_bar

    
#our ORAM test
def _real_oram_test(oram_size):

    oram = ORAM(oram_size)
    oram.cleanWriteMemory()
    # allocating memory shouldn't count as 'writing'...
    reset_counters()
    oram.initial_build('testing_data')
    for i in range(int(oram_size)-1):
        oram.access('write',int(i).to_bytes(oram.conf.KEY_SIZE,'big'),int(i+3).to_bytes(oram.conf.BALL_DATA_SIZE,'big'))
        if i % 10_000 == 0:
            update_loading_bar(i/oram_size)


def real_oram_test():
    number_of_MB = int(input('How many MB of storage should the test allocate?\n'))

    # The amount of data in each block is 16 bytes
    number_of_blocks = int((number_of_MB*(2**20))/16)
    
    print('Executing',number_of_blocks,'accesses (the size of the ORAM as every block contains 16bytes of data)')
    if number_of_MB > 50:
        print('Due to the initial build it might take several minutes before accesses begin.')
    
    if number_of_MB > 1000:
        print('Due to the initial build it might take several hours before accesses begin.')

    _real_oram_test(number_of_blocks)
    
    print('\naccesses: ', number_of_blocks) 
    
    Blocks_read = local_RAM.BALL_READ+local_RAM.BALL_WRITE
    print('Blocks-read: ', Blocks_read)
    
    print('Average blocks read per-access:', int(Blocks_read/number_of_blocks), 'Blocks')
    
    # The multiplication and then division of 10 is to make it show only one digit after the decimal point
    print('Average KB per-access:', int((10*32*Blocks_read/number_of_blocks)/1024)/10, 'KB')

    # Here we divide by 2 because the definition of a round trip is read-process-write
    print('Average round-trips per-access:', int((local_RAM.RT_READ+local_RAM.RT_WRITE)/(2*number_of_blocks)))


