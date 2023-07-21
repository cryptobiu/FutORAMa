from counter_only.ORAM import ORAM
from counter_only.RAM.local_RAM import local_RAM
from loading_bar import update_loading_bar

def _counter_only_test(oram_size):

    oram = ORAM(oram_size)

    oram.initial_build('testing_data')
    for i in range(0,oram_size-1,oram.conf.MU):
        btc = oram.built_tables_count()

        # Reading 2MU before building a level.
        local_RAM.BALL_READ += 4*btc*oram.conf.MU
        local_RAM.RT_READ += 2*btc*oram.conf.MU
        local_RAM.BALL_WRITE += 4*btc*oram.conf.MU
        local_RAM.RT_WRITE += 2*btc*oram.conf.MU
        oram.rebuild()
        if int(i/oram.conf.MU) % 100 == 0:
            update_loading_bar(i/oram_size)

def counter_only_test():
    number_of_MB = int(input('How many MB of storage should the test simulate?\n'))
    
    # The amount of data in each block is 16 bytes
    number_of_blocks = int((number_of_MB*(2**20))/16)
    
    print('Simulating',number_of_blocks,'accesses (the size of the ORAM as every block contains 16bytes of data)')
    if number_of_MB > 5_000_000:
        print('Due to the initial build it might take several minutes before accesses begin.')
    
    if number_of_MB > 1_000_000_000:
        print('Due to the initial build it might take several hours before accesses begin.')

    _counter_only_test(number_of_blocks)
    
    print('\naccesses: ', number_of_blocks) 
    
    Blocks_read = local_RAM.BALL_READ+local_RAM.BALL_WRITE
    print('Blocks-read: ', Blocks_read)
    
    print('Average blocks read per-access:', int(Blocks_read/number_of_blocks), 'Blocks')
    
    # The multiplication and then division of 10 is to make it show only one digit after the decimal point
    print('Average KB per-access:', int((10*32*Blocks_read/number_of_blocks)/1024)/10, 'KB')

    # Here we divide by 2 because the definition of a round trip is read-process-write
    print('Average round-trips per-access:', int((local_RAM.RT_READ+local_RAM.RT_WRITE)/(2*number_of_blocks)))

