This directory contains table schemas for each table in the OPUS database. The
files are in JSON format and contain a list of dictionaries describing the table
columns. Each dictionary can contain the following fields:

'@field_name'           The raw name of the new column

'@field_type'           One of:
                          'int1', 'int2', 'int4', 'int8'
                          'uint1', 'uint2', 'uint4', 'uint8'
                          'real4', 'real8'
                          'charNNN' (fixed-length char field)
                          'enum'
                          'timestamp' (implies ON UPDATE CURRENT_TIMESTAMP)

'@field_x_enum_options' If field_type == 'enum' this field must be included.
                        It contains a comma-separated list of enum values.

'@field_x_notnull'      If present and True, this field may not be NULL.

'@field_x_default'      If present, this is the default for the column. A None
                        value or 'NULL' means SQL NULL.

'@field_x_key'          If present and not False, this can contain:
                        'unique': This is a unique key
                        'primary': This is the primary key
                        'foreign': This is a foreign key; field_x_foreign_key
                                   must also be present
'@field_x_foreign_key'  If present, this key is a foreign key. The value is a
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

For an obs_XXX table, columns that directly correspond to a PDS INDEX field
may contain:

'description'           The text description of the PDS

For an obs_XXX table, information about how to populate the field MUST be
included:

'data_source'           A tuple (source, data). Source can be one of:
      'CONSTANT' in which case the data is the constant value.
      '<PDS TABLE NAME>' in which case the data is the field name in the
                        referenced PDS table, which must have already been
                        read as part of loading the volume.

Optional fields include:

'val_min'
'val_max'
