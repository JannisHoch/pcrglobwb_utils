# paths to files and dirs
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
grdc_file='..\examples\example_data\3629000_Obidos.day'
out_dir='..\examples\_validation_out\'

# execute script
python evaluate_output.py $nc_file $grdc_file $out_dir