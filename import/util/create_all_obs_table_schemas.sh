python obs_table_to_schema.py opus_small obs_general master_labels/COISS/index.lbl

python obs_table_to_schema.py opus_small obs_mission_cassini master_labels/COISS/index.lbl
python obs_table_to_schema.py opus_small obs_instrument_COCIRS master_labels/COCIRS/OBSINDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_COISS master_labels/COISS/index.lbl
python obs_table_to_schema.py opus_small obs_instrument_COUVIS master_labels/COUVIS/INDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_COVIMS master_labels/COVIMS/index.lbl

python obs_table_to_schema.py opus_small obs_mission_voyager master_labels/VGISS/INDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_VGISS master_labels/VGISS/INDEX.LBL

python obs_table_to_schema.py opus_small obs_mission_galileo master_labels/GOSSI/IMGINDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_GOSSI master_labels/GOSSI/IMGINDEX.LBL

python obs_table_to_schema.py opus_small obs_mission_hubble master_labels/HSTACS/INDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_HSTACS master_labels/HSTACS/INDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_HSTWFC3 master_labels/HSTWFC3/INDEX.LBL
python obs_table_to_schema.py opus_small obs_instrument_HSTWFPC2 master_labels/HSTWFPC2/INDEX.LBL
#python obs_table_to_schema.py opus_small obs_instrument_HSTSTIS master_labels/HSTSTIS/INDEX.LBL

python obs_table_to_schema.py opus_small obs_mission_new_horizons master_labels/NHLORRI/index.lbl
python obs_table_to_schema.py opus_small obs_instrument_LORRI master_labels/NHLORRI/index.lbl
mv ../table_schemas/obs_instrument_LORRI_proto.json ../table_schemas/obs_instrument_NHLORRI_proto.json
python obs_table_to_schema.py opus_small obs_instrument_MVIC master_labels/NHMVIC/index.lbl
mv ../table_schemas/obs_instrument_MVIC_proto.json ../table_schemas/obs_instrument_NHMVIC_proto.json

python obs_table_to_schema.py opus_small obs_ring_geometry master_labels/ring_geo/ring_geo.lbl
python obs_table_to_schema.py opus_small obs_surface_geometry__SATURN master_labels/surface_geo/surface_geo.lbl
mv ../table_schemas/obs_surface_geometry__SATURN_proto.json ../table_schemas/obs_surface_geometry_proto.json

python obs_table_to_schema.py opus_small obs_type_image master_labels/COISS/index.lbl
python obs_table_to_schema.py opus_small obs_wavelength master_labels/COISS/index.lbl
