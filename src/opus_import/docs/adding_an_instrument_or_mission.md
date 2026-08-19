To add a new instrument and/or mission:

- Edit config.py and modify:
    MISSION_ID_TO_MISSION
    INSTRUMENT_ID_TO_MISSION_ID
    BUNDLE_ID_PREFIX_TO_INSTRUMENT_ID

- If new weird tables need to be added, modify:
    TABLES_TO_POPULATE

- Add any parsing to instruments.py required to read the label files

- Create appropriate table_schemas (mission, instrument, new weird tables)

- Add new populate imports at the top of do_import.py

- Add any new functions to populate the new tables
