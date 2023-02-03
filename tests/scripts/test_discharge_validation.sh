# paths to files and dirs
nc_file='../../examples/example_data/GRDC/DUMMY_discharge_dailyTot_output.nc'
yaml_file='../../examples/example_data/GRDC/stations.yaml'
folder='../../examples/example_data/GRDC/files'
excel_file='../../examples/example_data/GRDC/Obidos_data.xlsx'
loc='../../examples/example_data/GRDC/stations.geojson'
yml_out_dir='eval_GRDC_GSIM/GRDC/from_yml/'
fld_out_dir='eval_GRDC_GSIM/GRDC/from_folder/'
sel_out_dir='eval_GRDC_GSIM/GRDC/from_folder_selectOnly/'
xls_out_dir='eval_GRDC_GSIM/GRDC/from_xls/'

# echo
# echo GRDC

# # execute script

# echo
# echo WITHOUT RESAMPLING FROM YAML-FILE - WITH POOLING
# pcru_eval_tims grdc $nc_file $yaml_file $yml_out_dir -e ascii -N 4  

# echo
# echo WITHOUT RESAMPLING FROM YAML-FILE - WITHOUT POOLING
# pcru_eval_tims grdc $nc_file $yaml_file $yml_out_dir/pooling -e ascii --verbose 

# echo
# echo WITHOUT RESAMPLING FROM FOLDER
# pcru_eval_tims grdc $nc_file $folder $fld_out_dir 

# # echo
# # echo WITHOUT RESAMPLING FROM EXCEL-FILE
# # pcru_eval_tims excel -v discharge -id station --plot --verbose $nc_file $excel_file $loc $xls_out_dir 

# echo 
# echo RESAMPLING TO MONTHLY DATA FROM YAML-FILE
# pcru_eval_tims grdc $nc_file $yaml_file $yml_out_dir -t M  

# echo 
# echo RESAMPLING TO YEARLY DATA FROM YAML-FILE
# pcru_eval_tims grdc $nc_file $yaml_file $yml_out_dir -t Y

folder='../../examples/example_data/GSIM/files'
fld_out_dir='eval_GRDC_GSIM/GSIM/from_folder/'

echo
echo GSIM

echo
echo WITHOUT RESAMPLING FROM FOLDER
pcru_eval_tims gsim $nc_file $folder $fld_out_dir --verbose
