


import math
from counter_only.RAM.local_RAM import local_RAM
from counter_only.config import config
from counter_only.hashTable import HashTable

class ORAM:

    def __init__(self, number_of_blocks) -> None:
        self.not_found = 0
        
        # power of two number of bins:
        number_of_blocks = (2**math.ceil(math.log(number_of_blocks/config.MU,2)))*config.MU
        self.conf = config(number_of_blocks)
        
        self.local_stash = {}
        self.stash_reals_count = 0
        
        self.read_count = 0
        self.tables:list[HashTable]= []
        current_number_of_blocks = config.MU
        while current_number_of_blocks <= number_of_blocks:
            self.tables.append(HashTable(config(current_number_of_blocks)))
            current_number_of_blocks *= 2
    
    def built_tables_count(self):
        count = 0
        for table in self.tables:
            if table.is_built:
                count += 1
        return count
    
    def initial_build(self, data_location) -> None:
        final_table = self.tables[-1]
        temp = final_table.data_ram
        self.original_data_ram = local_RAM(data_location, final_table.conf)
        final_table.data_ram = self.original_data_ram
        final_table.rebuild(final_table.conf.N)
        final_table.data_ram = temp
        
    def access(self, op,  key, value = None) -> bytes:
        print('no need to implement in count-only because the tests counts the cost of an access')
        # no need to implement in count-only because the tests counts the cost of an access
    
    def rebuild(self):
        
        if not self.tables[0].is_built:
            self.rebuildLevelOne()
            return
        
        # extract built layers
        self.extractLevelOne()
        for table in self.tables[1:]:
            if table.is_built:
                table.extract()
            else:
                break
        
        
        for i in range(1, len(self.tables)):
            previous_table = self.tables[i-1]
            current_table = self.tables[i]
            if current_table.is_built:
                current_table.intersperse()
                current_table.is_built = False
            else:
                current_table.data_ram = previous_table.bins_ram
                current_table.rebuild(0)
                return
        final_table = self.tables[-1]
        
        # for purposes of efficiency, in the final build - the write locations switch...
        final_table.conf.FINAL = True
        final_table.binsTightCompaction([final_table.conf.DUMMY_STATUS, final_table.conf.SECOND_DUMMY_STATUS])
        final_table.rebuild(final_table.conf.N)
    
    def extractLevelOne(self):
        hash_table_one = self.tables[0]
        hash_table_one.is_built = False 
        local_RAM.BALL_READ += self.conf.BIN_SIZE
        local_RAM.RT_READ += 1
        local_RAM.BALL_WRITE += self.conf.BIN_SIZE
        local_RAM.RT_WRITE += 1         
    
    def rebuildLevelOne(self):
        hash_table_one = self.tables[0]
        local_RAM.BALL_WRITE += hash_table_one.conf.BIN_SIZE
        local_RAM.RT_WRITE += 1
        hash_table_one.is_built = True
        
        
            