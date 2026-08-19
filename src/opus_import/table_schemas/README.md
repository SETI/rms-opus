This directory contains table schemas for each table in the OPUS database. The
files are in JSON format and contain a list of dictionaries describing the table
columns. Each dictionary can contain the following fields:

'field_name'            The raw name of the new column

'field_type'            One of:
                          'int1', 'int2', 'int4', 'int8'
                          'uint1', 'uint2', 'uint4', 'uint8'
                          'real4', 'real8'
                          'charNNN' (fixed-length char field)
                          'varcharNNN' (variable-length char field)
                          'text' (arbitrary-length char field)
                          'mult_idx' (mult field - int idx into associated mult table)
                          'mult_list' (mult field - JSON list of int idx into associated
                                       mult table)
                          'enum'
                          'flag_yesno' (Enum 'Yes','No','N/A')
                          'flag_onoff' (Enum 'On','Off','N/A')
                          'timestamp' (implies ON UPDATE CURRENT_TIMESTAMP)
                          'datetime'

'field_enum_options'    If field_type == 'enum' this field must be included.
                        It contains a comma-separated list of enum values.

'field_notnull'         If present and True, this field may not be NULL.

'field_default'         If present, this is the default for the column. A None
                        value or 'NULL' means SQL NULL.

'field_key'             If present and not False, this can contain:
                        True: This is a normal index key
                        'unique': This is a unique key
                        'primary': This is the primary key
                        'foreign': This is a foreign key; field_foreign_key
                                   must also be present
'field_key_foreign'     If present, this key is a foreign key. The value is a
                        tuple (foreign_table_name, foreign_column_name)

For an obs_XXX table, param_info fields may be included:
  'pi_category_name'
  'pi_units'
  'pi_display'
  'pi_display_results'
  'pi_disp_order'
  'pi_sub_heading'
  'pi_label'
  'pi_label_results'
  'pi_intro'
  'pi_tooltip'
  'pi_slug'

  'pi_dict_context'
  'pi_dict_name'
  'definition'

For an obs_XXX table, information about how to populate the field MUST be
included:

'data_source'            A tuple (source, data). Source can be one of:

      'IGNORE'
      'TAB:<TABLE_NAME>' in which case the data is the field name in the
                         referenced PDS or internal table, which must have
                         already been read as part of loading the bundle/volume.
      'ARRAY:<TABLE_NAME>' in which case the data is the field name in the
                        referenced PDS or internal table, which must have
                        already been read as part of loading the bundle/volume,
                        then ':', then the number of the array element.
      'FUNCTION'         in which case the data is the name of the function
                         to execute. <INST> and <MISSION> are substituted.
                         If the function name starts with "~" then it is
                         not an error if the function doesn't exist.
      'MAX_ID'           in which case the data is ignored. The value used
                         is the largest id used for that table so far + 1.
      'VALUEINT'         in which case the value is the explicitly given int.
      'VALUEREAL'        in which case the value is the explicitly given float.
      'VALUESTR'         in which case the value is the explicitly given string.

    There can also be more than one pair of items in the tuple, in which case
    they are tried in order. If the first one fails because the field or
    function doesn't exist, then the next pair is tried, and so on.

Optional fields include:

'val_min'
'val_max'
'val_sentinel'
