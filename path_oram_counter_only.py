from counter_only.PathORAM.path_ORAM import PathORAM

def path_oram_counter_only_test():
    number_of_MB = int(input('How many MB of storage should the test simulate?\n'))
    block_size = int(input('What is the block size in bytes?\n'))
    
    # The amount of data in each block is 16 bytes
    number_of_blocks = int((number_of_MB*(2**20))/block_size)
    
    print(f'Simulating a generic access (the size of the ORAM as every block contains {block_size}bytes)')

    path_oram = PathORAM(block_size, number_of_blocks, False)
    
    print('Blocks read per-access:', 2*path_oram.number_of_blocks_per_access(), 'Blocks')
    
    # The multiplication and then division of 10 is to make it show only one digit after the decimal point
    print('KB per-access:', int(10*2*path_oram.number_of_bytes_per_access()/1024)/10, 'KB')

    print('Round-trips per-access:',  2*path_oram.number_of_levels())

