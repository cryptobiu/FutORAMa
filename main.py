# run instructions:
# works for me on windows 11.
# python version 3.10.5
# installations needed:
# pip install pycryptodomex==3.15.0
# pip install numpy==1.23.1 (not necessary, this is just the version I used)

from counter_only_tests import counter_only_test
from real_oram_tests import real_oram_test
from path_oram_counter_only import path_oram_counter_only_test
from path_oram_tests import path_oram_tests

test_type = int(input('Enter test type:\n1) Real ORAM accesses\n2) Simulated accesses to calculate the approximate bandwidth and round-trips\n3) Path-ORAM comparison (counter only)\n4) actual Path-ORAM run\n'))
if test_type == 1:
    real_oram_test()
elif test_type == 2:
    counter_only_test()
elif test_type == 3:
    path_oram_counter_only_test()
else:
    path_oram_tests()