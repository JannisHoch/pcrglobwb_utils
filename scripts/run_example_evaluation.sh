# paths to files and dirs
path_to_script='.'
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
out_dir='benchmark_out'

# execute script
python $path_to_script/evaluate_output.py $nc_file $out_dir -g $grdc_file