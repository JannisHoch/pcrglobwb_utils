# paths to files and dirs
path_to_script='.'
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
out_dir='validation_out_with_grdc'

# execute script
python $path_to_script/evaluate_output.py $nc_file $out_dir -g $grdc_file

# paths to files and dirs
path_to_script='.'
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
excel_file='..\examples\example_data\Obidos_data.xlsx'
latitude=-1.9472
longitude=-55.5111
out_dir='validation_out_with_excel'

# execute script
python $path_to_script/evaluate_output.py $nc_file $out_dir -e $excel_file -lat $latitude -lon $longitude