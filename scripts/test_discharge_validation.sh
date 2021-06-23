# paths to files and dirs
script='./evaluate_timeseries.py'
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
out_dir='eval_GRDC'

# execute script
python $script -g $grdc_file --plot -t month $nc_file $out_dir 
python $script -g $grdc_file --plot -t year $nc_file $out_dir
python $script -g $grdc_file --plot -t quarter $nc_file $out_dir