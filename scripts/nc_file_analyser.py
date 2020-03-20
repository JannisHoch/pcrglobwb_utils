import pcrglobwb_utils as pcru
import os, sys

ncfiles_list = sys.argv[1:-2]
grdc_file = sys.argv[-1]

for file in ncfiles_list:
    print(str(file)