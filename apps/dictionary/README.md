# Dictionary

The Dictionary app is a stand-alone Django web interface that allows users to view and search the combined PDSS and other definition/term database as a dictionary.

The dictionary uses two tables to present the information to the user:
  Contexts - provides a mapping of the context to a human-readable text description of the mission or instrument    contexts
  Dictionary - provides a mapping of term + context to present a term definition.  In addition, some terms have 'subterms', or lists of selectable options, that will have 'hover text' descriptions.

The Dictionary table is generated from multiple files - the main file comes from the PDSS data:  https://pds.jpl.nasa.gov/tools/dictionary.shtml.  This data is updated approx. 3 times per year.  Note that the file 'pdsdd.full' at this time must be hand edited to only include the objects identified as "ELEMENT_DEFINITION" to work properly w/the pdsparser.

In addition to the PDSS data, definitions are made available from the .json files used during data import.  These files are available in the subfolder: import\table_schemas.  The fields used from the .json files are:  pi_dict_name, pi_dict_context, description, mult_options <optional field>.

Mult_options are used to create specialized labels and helping 'hover text' over the subterms in the widgets.  There are currently 6 fields per row in each mult_option:
    Unique ID
    Value in database
    Label to show to user
    Display order
    Display or not
    Hover text

The dictionary import uses the 'value' field in the 'subterm' field to signify this is a definition for a subterm; hover text is used as the 'definition' field contents for that row in the table.

The index for the dictionary table is unique on the three fields: term + context + subterm.  Note that where there is no subterm, the default value is ""  <not null, as a null field cannot be used as part of an index>.

To import data into the dictionary, copy secrets_template.py into config.py and update the parameters for the DB login, username, etc. and set up the paths, as required.  Python 3.6 compliant.

python importUtils.py
