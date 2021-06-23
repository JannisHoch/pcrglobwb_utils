# paths to files and dirs
script=pcr_eval_timeseries
nc_file='..\../examples\example_data\GRDC\DUMMY_discharge_dailyTot_output.nc'
yaml_file='../../examples/example_data/GRDC/stations.yaml'
out_dir='eval_GRDC'

# execute script
echo
echo WITHOUT RESAMPLING
$script -y $yaml_file --plot $nc_file $out_dir 
echo 
echo RESAMPLING TO MONTHLY DATA
$script -y $yaml_file --plot -t month $nc_file $out_dir 
echo 
echo RESAMPLING TO YEARLY DATA
$script -y $yaml_file --plot -t year $nc_file $out_dir
echo 
echo RESAMPLING TO QUARTERLY DATA
$script -y $yaml_file --plot -t quarter $nc_file $out_dir