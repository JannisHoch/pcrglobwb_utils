# paths to files and dirs
nc_file='..\../examples\example_data\GRDC\DUMMY_discharge_dailyTot_output.nc'
yaml_file='../../examples/example_data/GRDC/stations.yaml'
folder='../../examples/example_data/GRDC/files'
excel_file='../../examples/example_data/GRDC/Obidos_data.xlsx'
loc='../../examples/example_data/GRDC/stations.geojson'
yml_out_dir='eval_GRDC/from_yml/'
fld_out_dir='eval_GRDC/from_folder/'
xls_out_dir='eval_GRDC/from_xls/'

# execute script
echo
echo WITHOUT RESAMPLING FROM YAML-FILE
pcru_eval_tims --version grdc -y $yaml_file -e ascii --plot --verbose $nc_file $yml_out_dir 

echo
echo WITHOUT RESAMPLING FROM FOLDER
pcru_eval_tims grdc -f $folder --plot $nc_file $fld_out_dir 

echo
echo WITHOUT RESAMPLING FROM EXCEL-FILE
pcru_eval_tims excel -v discharge -id station --plot --verbose $nc_file $excel_file $loc $xls_out_dir 

echo 
echo RESAMPLING TO MONTHLY DATA FROM YAML-FILE
pcru_eval_tims grdc -y $yaml_file --plot -t month $nc_file $yml_out_dir 

echo 
echo RESAMPLING TO YEARLY DATA FROM YAML-FILE
pcru_eval_tims grdc -y $yaml_file --plot -t year $nc_file $yml_out_dir

echo 
echo RESAMPLING TO QUARTERLY DATA FROM YAML-FILE
pcru_eval_tims grdc -y $yaml_file --plot -t quarter $nc_file $yml_out_dir