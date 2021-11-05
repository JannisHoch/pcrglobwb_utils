######

nc_file='../../examples/example_data/GLEAM/totalEvaporation_monthTot_output_2010_Tanzania.nc'
poly='../../examples/example_data/Tanzania_shp/waterProvinces.geojson'
out_dir='eval_GLEAM/'

echo
echo CREATING POLYGON MASK
pcru_preprocess create-poly-mask -v total_evaporation -id watprovID --verbose $nc_file $poly $out_dir

#####

nc_file='../../examples/example_data/GRDC/DUMMY_discharge_dailyTot_output.nc'
folder='../../examples/example_data/GRDC/files'
sel_out_dir='eval_GRDC/from_folder_selectOnly/'

echo
echo SELECTING GRDC STATIONS
pcru_preprocess select-grdc-stations -y_thld 40 $folder $sel_out_dir
pcru_eval_tims grdc -f $folder -sf $sel_out_dir/selected_GRDC_stations.txt --plot $nc_file $sel_out_dir 