shp='../../examples/example_data/Tanzania_shp/waterProvinces.geojson'
obs='../../examples/example_data/GRACE/GRACE_data_2010_Tanzania.nc'
sim='../../examples/example_data/GRACE/totalWaterStorageThickness_monthAvg_output_2010_Tanzania.nc'
out='./eval_GRACE/pooling'

echo
echo VALIDATING WITH GRACE - WITHOUT POOLING

pcru_eval_poly -o lwe_thickness -s total_thickness_of_water_storage -cf 100 -id watprovID --plot --anomaly --verbose $shp $sim $obs $out

out='./eval_GRACE/pooling'

echo
echo VALIDATING WITH GRACE - WITH POOLING

pcru_eval_poly -o lwe_thickness -s total_thickness_of_water_storage -N 4 -cf 100 -id watprovID --plot --anomaly $shp $sim $obs $out


obs='../../examples/example_data/GLEAM/GLEAM_data_2010_Tanzania.nc'
sim='../../examples/example_data/GLEAM/totalEvaporation_monthTot_output_2010_Tanzania.nc'
out='./eval_GLEAM'

echo
echo VALIDATING WITH GLEAM

pcru_eval_poly -o E -s total_evaporation -cf 1000 -id watprovID --plot $shp $sim $obs $out