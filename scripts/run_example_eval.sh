# paths to files and dirs
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
out_dir='..\examples\_out\'

# execute script
python nc_file_analyser.py $nc_file $grdc_file $out_dir