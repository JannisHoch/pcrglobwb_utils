# paths to files and dirs as well as settings
nc_file='..\examples\example_data\DUMMY_discharge_dailyTot_output.nc'
row=17
col=50
out_dir='..\examples\_benchmark_out\'

# execute script
python benchmark_output.py $nc_file $nc_file $nc_file $row $col $out_dir