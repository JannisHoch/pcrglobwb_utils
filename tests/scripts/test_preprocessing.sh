######

nc_file='../../examples/example_data/GLEAM/totalEvaporation_monthTot_output_2010_Tanzania.nc'
obs='../../examples/example_data/GLEAM/GLEAM_data_2010_Tanzania.nc'
poly='../../examples/example_data/Tanzania_shp/waterProvinces.geojson'
out_dir='eval_GLEAM_withMasks/'
fname_PCR='waterProvince_masks_PCR.list'
fname_GLEAM='waterProvince_masks_GLEAM.list'

echo
echo CREATING POLYGON MASK
pcru_preprocess create-poly-mask -of $fname_PCR -v total_evaporation -id watprovID --verbose $nc_file $poly $out_dir/masks_PCR
pcru_preprocess create-poly-mask -of $fname_GLEAM -v E -id watprovID --verbose $obs $poly $out_dir/masks_GLEAM
echo
pcru_eval_poly -o E -s total_evaporation -sm $out_dir/masks_PCR/$fname_PCR -om $out_dir/masks_GLEAM/$fname_GLEAM -cf 1000 -id watprovID --plot --verbose $poly $nc_file $obs $out_dir

#####

nc_file='../../examples/example_data/GRDC/DUMMY_discharge_dailyTot_output.nc'
folder='../../examples/example_data/GRDC/files'
sel_out_dir='eval_GRDC/from_folder_selectOnly/'

echo
echo SELECTING GRDC STATIONS
pcru_preprocess select-grdc-stations -y_thld 40 $folder $sel_out_dir
echo
pcru_eval_tims grdc -f $folder -sf $sel_out_dir/selected_GRDC_stations.txt --plot $nc_file $sel_out_dir 