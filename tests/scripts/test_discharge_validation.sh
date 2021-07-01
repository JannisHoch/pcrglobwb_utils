# paths to files and dirs
nc_file='..\../examples\example_data\GRDC\DUMMY_discharge_dailyTot_output.nc'
yaml_file='../../examples/example_data/GRDC/stations.yaml'
out_dir='eval_GRDC'

# execute script
echo
echo WITHOUT RESAMPLING
pcr_utils_evaluate --version grdc -y $yaml_file --plot $nc_file $out_dir 
echo 
echo RESAMPLING TO MONTHLY DATA
pcr_utils_evaluate grdc -y $yaml_file --plot -t month $nc_file $out_dir 
echo 
echo RESAMPLING TO YEARLY DATA
pcr_utils_evaluate grdc -y $yaml_file --plot -t year $nc_file $out_dir
echo 
echo RESAMPLING TO QUARTERLY DATA
pcr_utils_evaluate grdc -y $yaml_file --plot -t quarter $nc_file $out_dir