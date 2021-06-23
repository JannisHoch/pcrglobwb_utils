# paths to files and dirs
script='./evaluate_timeseries.py'
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
out_dir='eval_GRDC'

# execute script
echo
echo WITHOUT RESAMPLING
python $script -g $grdc_file --plot $nc_file $out_dir 
echo 
echo RESAMPLING TO MONTHLY DATA
python $script -g $grdc_file --plot -t month $nc_file $out_dir 
echo 
echo RESAMPLING TO YEARLY DATA
python $script -g $grdc_file --plot -t year $nc_file $out_dir
echo 
echo RESAMPLING TO QUARTERLY DATA
python $script -g $grdc_file --plot -t quarter $nc_file $out_dir