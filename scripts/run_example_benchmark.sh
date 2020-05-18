# paths to files and dirs as well as settings
path_to_script='.'
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
lon=-55.511100
lat=-1.947200
out_dir='benchmark_out'

# execute script
python $path_to_script/benchmark_output.py -n $nc_file -n $nc_file -n $nc_file -lon $lon -lat $lat $out_dir