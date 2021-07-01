# paths to files and dirs
nc_file='..\../examples\example_data\GRDC\DUMMY_discharge_dailyTot_output.nc'
yaml_file='../../examples/example_data/GRDC/stations.yaml'
folder='../../examples/example_data/GRDC/files'
yml_out_dir='eval_GRDC/from_yml/'
fld_out_dir='eval_GRDC/from_folder/'

# execute script
echo
echo WITHOUT RESAMPLING FROM YAML-FILE
pcr_utils_evaluate --version grdc -y $yaml_file --plot --verbose $nc_file $yml_out_dir 

echo
echo WITHOUT RESAMPLING FROM FOLDER
pcr_utils_evaluate --version grdc -f $folder --plot $nc_file $fld_out_dir 

echo 
echo RESAMPLING TO MONTHLY DATA FROM YAML-FILE
pcr_utils_evaluate grdc -y $yaml_file --plot -t month $nc_file $yml_out_dir 

echo 
echo RESAMPLING TO YEARLY DATA FROM YAML-FILE
pcr_utils_evaluate grdc -y $yaml_file --plot -t year $nc_file $yml_out_dir

echo 
echo RESAMPLING TO QUARTERLY DATA FROM YAML-FILE
pcr_utils_evaluate grdc -y $yaml_file --plot -t quarter $nc_file $yml_out_dir