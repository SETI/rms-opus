"""The root of the obs class hierarchy: one instance computes one bundle's rows.

`ObsBase` is what every obs class ultimately derives from. It owns three things the rest
of the hierarchy is built out of: the per-observation metadata an instrument's field
methods read, the helpers that read a value out of one of the PDS index tables that
metadata is assembled from, and `ObsBase._create_mult`, which builds the dictionary a
group column's field method has to return.

It also declares, as methods that raise `NotImplementedError`, the handful of things
only a PDS3 or PDS4 subclass or a specific instrument can answer -- what the instrument
is, where its primary data file lives, and how to turn an index row into a file
specification. The hierarchy layers those in: `opus_import.obs.obs_base_pds3` and
`opus_import.obs.obs_base_pds4` answer the PDS-version questions, one module per OPUS
table adds that table's field methods, a mission module adds what a mission shares, and
a bundle module answers what only one bundle knows.

One instance is created per bundle, not per observation:
`opus_import.steps.do_import_index` replaces the `metadata` dictionary in place for each
row it reads, so no method may cache anything derived from it. `ObsBase.opus_id` shows
what caching is allowed to look like -- it re-derives whenever the file specification it
was computed from changes.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from opus_import import config_targets, import_util
from opus_import.obs.field_types import FloatField, MultField

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import pdsfile

    from opus_import.context import ImportContext
    from opus_import.import_util import IndexRow

TargetInfo = tuple[str | None, str, str]
"""A `opus_import.config_targets.TARGET_NAME_INFO` entry: planet id, class, and name."""


class ObsBase:
    """What every obs class shares: the metadata, the index readers, and the mult maker.

    Attributes are private by convention; a subclass reads the metadata through the
    ``_*_col`` helpers rather than reaching into it, because those apply the ``pdstable``
    mask that marks a value as missing.
    """

    def __init__(
        self, ctx: ImportContext, bundle: str | None = None, metadata: dict[str, Any] | None = None
    ) -> None:
        """Initialize an ObsBase object.

        Parameters:
            ctx: The ImportContext for this import run. An obs class uses it only to
                log and to read the run's arguments; it never reaches the database
                through it, which is what lets
                `opus_import.steps.do_import_obs.import_run_field_function` treat a
                field method's exception as a bad field rather than an aborted import.
            bundle: The PDS3 volume ("COISS_2116") or PDS4 bundle.
            metadata: The collection of metadata available for this observation. This
                includes rows from the various index as well as additional information.
                Note that the metadata structure is updated for each observation even
                though only a single ObsBase instance is created for each bundle/volume.
                Thus methods have to assume that the metadata has changed between calls
                and they can't cache results. It is None while the tables are being
                created, before any observation has been read.
        """
        self._ctx = ctx
        self._bundle = bundle
        self._metadata = metadata
        # --import-ignore-errors, read off the run's arguments rather than taken as a
        # constructor argument, so that every construction site reaches the two branches
        # that consult it -- an unknown target name here and in
        # `opus_import.obs.obs_cassini_common_pds3` -- without having to pass it on.
        # Read eagerly, so a context built without real parsed arguments fails at
        # construction rather than only on the rare error path that needs the flag.
        self._ignore_errors = ctx.args.import_ignore_errors

        self._opus_id_last_filespec: str | None = None  # For caching opus_id
        self._opus_id_cached: str | None = None

    ###################################
    ### !!! Must override these !!! ###
    ###################################

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, such as ``'COISS'``.

        Returns:
            The id, or None for a bundle whose instrument is not known until an
            observation has been read -- which is what decides that no
            ``obs_instrument_*`` table is created for it.

        Raises:
            NotImplementedError: Always; an instrument class must override this.
        """
        raise NotImplementedError

    @property
    def inst_host_id(self) -> str:
        """The OPUS instrument host id, such as ``'CO'``.

        Raises:
            NotImplementedError: Always; an instrument class must override this.
        """
        raise NotImplementedError

    @property
    def mission_id(self) -> str:
        """The OPUS mission id, such as ``'CO'``.

        It selects the ``obs_mission_*`` table this bundle is imported into, through
        `opus_import.config_data.MISSION_ID_TO_MISSION_TABLE_SFX`.

        Raises:
            NotImplementedError: Always; an instrument class must override this.
        """
        raise NotImplementedError

    @property
    def primary_filespec(self) -> str | None:
        """The path, relative to the holdings root, of this observation's data file.

        Everything that identifies an observation is derived from it: the OPUS id, the
        browse products, and the cross-references between index files.

        Returns:
            The path, or None for an index row that names no data file, which an
            instrument whose index can carry such a row returns.

        Raises:
            NotImplementedError: Always; an instrument class must override this.
        """
        raise NotImplementedError

    def primary_filespec_from_index_row(
        self,
        row: IndexRow,
        convert_lbl: bool = False,
        add_phase_from_row: bool = False,
        add_phase_from_inst: bool = False,
    ) -> str | None:
        """Build a file specification from a row of any of this bundle's index files.

        This is how a supplemental, geometry or inventory index row is matched up with
        the primary index row for the same observation, since those files do not agree
        on how they spell a file specification.

        Parameters:
            row: The index row to read.
            convert_lbl: True to run the result through
                `ObsBase.convert_filespec_from_lbl`.
            add_phase_from_row: True to append the phase read from this row, which is
                what distinguishes the IR and VIS rows COVIMS geometry indexes carry per
                observation.
            add_phase_from_inst: True to append this instance's own phase instead, which
                is what the same COVIMS case needs when looking a row up.

        Returns:
            The file specification, or None for a row that names no file. The PDS3
            implementation logs why; the PDS4 one does not, because a PDS4 index row
            either carries the path or is not a row OPUS imports.

        Raises:
            NotImplementedError: Always; a PDS-version subclass must override this.
        """
        raise NotImplementedError

    def _pdsfile_from_filespec(self, filespec: str) -> pdsfile.PdsFile:
        """Return the ``pdsfile`` object for a file specification.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            A ``Pds3File`` or ``Pds4File``, which is what supplies the OPUS id and the
            browse products. ``PdsFile`` is the base both derive from, so it is what
            the two overrides have in common. It is not checked: ``pdsfile`` ships no
            annotations, so it sits in ``ignore_missing_imports`` in pyproject.toml and
            the checker resolves this name to ``Any``.

        Raises:
            NotImplementedError: Always; a PDS-version subclass must override this.
        """
        raise NotImplementedError

    def _time_from_some_index(self, column: str = '') -> FloatField:
        """Read an observation's start time from whichever index carries it.

        Parameters:
            column: The column holding the start time. Each PDS-version subclass
                supplies its own default, since PDS3 and PDS4 spell the column
                differently; the value here is never used, because this raises.

        Returns:
            The time in seconds TAI, or None if it is missing or unparsable.

        Raises:
            NotImplementedError: Always; a PDS-version subclass must override this.
        """
        raise NotImplementedError

    def _time2_from_some_index(self, time1: FloatField, column: str = '') -> FloatField:
        """Read an observation's stop time from whichever index carries it.

        Parameters:
            time1: The start time, so a stop time that precedes it can be caught.
            column: The column holding the stop time, defaulted per PDS version as in
                `ObsBase._time_from_some_index`.

        Returns:
            The time in seconds TAI, or None if it is missing or unparsable.

        Raises:
            NotImplementedError: Always; a PDS-version subclass must override this.
        """
        raise NotImplementedError

    #############################
    ### Public access methods ###
    #############################

    def __str__(self) -> str:
        """Return the class, bundle and error handling, for a debugging dump."""
        s = 'class ' + type(self).__name__ + '\n'
        s += '  bundle = ' + str(self._bundle) + '\n'
        s += '  ignore_errors = ' + str(self._ignore_errors) + '\n'
        return s

    @property
    def bundle(self) -> str | None:
        """The bundle or volume being imported, or None if none was given."""
        return self._bundle

    @property
    def phase_name(self) -> Any:
        """The phase of the current observation, from `ObsBase.phase_names`."""
        assert self._metadata is not None
        return self._metadata['phase_name']

    @property
    def opus_id(self) -> str | None:
        """The OPUS id of the current observation.

        Returns:
            The id, or None if there is no primary file specification or ``pdsfile``
            could not derive an id from it, either of which is logged as an error.
        """
        filespec = self.primary_filespec
        # The None check comes first because the cache starts at (None, None): a
        # missing filespec would otherwise match the empty cache and return None as a
        # hit, so the very first invalid observation is the one that goes unreported.
        if filespec is None:
            self._log_nonrepeating_error(
                'Unable to create OPUS_ID: this observation has no filespec'
            )
            return None
        if filespec == self._opus_id_last_filespec:
            # Creating the OPUS ID can be expensive so we cache it here because
            # it is used for every obs_ table.
            return self._opus_id_cached
        pdsf = self._pdsfile_from_filespec(filespec)
        opus_id: str | None = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_error(f'Unable to create OPUS_ID using filespec {filespec}')
            return None
        self._opus_id_last_filespec = filespec
        self._opus_id_cached = opus_id
        return opus_id

    def opus_id_from_index_row(self, row: IndexRow) -> str | None:
        """Return the OPUS id an index row describes.

        This is a helper function used to take a row from the supplemental_index and
        convert it to an opus_id so that the supplemental_index and other
        index/geo/inventory files can be cross-referenced. We do this here because the
        supplemental index files are inconsistent in their formatting.

        Parameters:
            row: The index row to read.

        Returns:
            The OPUS id, or None if the row names no file or its file specification
            does not resolve to an id. Both are logged as a warning rather than an
            error, because an index can legitimately name files OPUS does not import.
        """
        full_filespec = self.primary_filespec_from_index_row(row)
        if full_filespec is None:
            self._log_nonrepeating_warning(
                'Unable to create OPUS_ID from index: the row names no file'
            )
            return None
        try:
            pdsf = self._pdsfile_from_filespec(full_filespec)
        except KeyError:
            self._log_nonrepeating_warning(
                'Unable to create OPUS_ID from index '
                + f'using filespec {full_filespec} - internal PdsFile crash'
            )
            return None
        opus_id: str | None = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_warning(
                f'Unable to create OPUS_ID from index using filespec {full_filespec}'
            )
            return None
        return opus_id

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a file specification naming a label to one naming the data file.

        Parameters:
            filespec: The path to convert.

        Returns:
            The path unchanged. The data file's extension is instrument-specific, so an
            instrument whose primary file specification names a ``.LBL`` file overrides
            this.
        """
        return filespec

    @property
    def phase_names(self) -> list[str]:
        """The phases each index row is expanded into.

        Returns:
            A single empty string, meaning one observation per index row. An instrument
            whose index row describes several observations -- COVIMS, whose rows carry
            both an IR and a VIS observation -- overrides this with one name per
            observation, and every field method is then called once per name with
            `ObsBase.phase_name` set to it.
        """
        return ['']

    def surface_geo_target_list(self) -> Sequence[str] | None:
        """The targets this observation has surface geometry for.

        Returns:
            None, meaning the surface geometry comes from separate summary files, one
            per target. An instrument that carries it inline overrides this with the
            target names, and its surface geometry field methods are then called once
            per name.
        """
        return None

    ### Helpers for other data_sources ###

    def compute_longitude_field(self) -> FloatField:
        """Return the center of the longitude range a column pair describes.

        This is the value a ``LONGITUDE_FIELD`` data source asks for. Storing the center
        and the span rather than the endpoints is what lets a search wrap around zero.

        Returns:
            The center longitude in degrees, normalized to ``[0, 360)``, or None if
            either endpoint is missing.
        """
        assert self._metadata is not None
        field_name = self._metadata['field_name']
        table_name = self._metadata['table_name']
        row = self._metadata[table_name + '_row']

        assert not field_name.startswith('d_'), (table_name, field_name)

        long1 = row[field_name + '1']
        long2 = row[field_name + '2']

        if long1 is None or long2 is None:
            return None

        if long2 >= long1:
            the_long = (long1 + long2) / 2.0
        else:
            the_long = (long1 + long2 + 360.0) / 2.0

        if the_long >= 360:
            the_long -= 360.0
        if the_long < 0:
            the_long += 360.0

        center: float = the_long
        return center

    def compute_d_longitude_field(self) -> FloatField:
        """Return half the span of the longitude range a column pair describes.

        This is the value a ``D_LONGITUDE_FIELD`` data source asks for, and the
        companion of `ObsBase.compute_longitude_field`.

        Returns:
            Half the span in degrees, or None if either endpoint is missing.
        """
        assert self._metadata is not None
        field_name = self._metadata['field_name']
        table_name = self._metadata['table_name']
        row = self._metadata[table_name + '_row']

        assert field_name.startswith('d_'), (table_name, field_name)

        field_name = field_name[2:]  # Get rid of d_

        long1 = row[field_name + '1']
        long2 = row[field_name + '2']

        if long1 is None or long2 is None:
            return None

        if long2 >= long1:
            the_long = (long1 + long2) / 2.0
        else:
            the_long = (long1 + long2 + 360.0) / 2.0

        half_span: float = the_long - long1
        return half_span

    ###############################
    ### Internal access methods ###
    ###############################

    def _index_col(self, col: str, idx: int | None = None) -> Any:
        """Read a column of the primary index row.

        Every ``_*_col`` helper returns whatever the PDS parser produced -- a string, a
        number, or None -- because a PDS index is untyped as far as this code is
        concerned. It is the field method calling it that declares, from its schema
        column, what the value is supposed to be.

        Parameters:
            col: The index column to read.
            idx: Which element to read from a column holding a sequence.

        Returns:
            The value, or None if the column is absent or masked as missing.
        """
        assert self._metadata is not None
        return import_util.safe_column(self._metadata['index_row'], col, idx=idx)

    def _has_supp_index(self) -> bool:
        """Whether this observation has a supplemental index row."""
        assert self._metadata is not None
        return 'supp_index_row' in self._metadata

    def _supp_index_col(self, col: str, idx: int | None = None) -> Any:
        """Read a column of the supplemental index row.

        Parameters:
            col: The index column to read.
            idx: Which element to read from a column holding a sequence.

        Returns:
            The value, as described in `ObsBase._index_col`.
        """
        assert self._metadata is not None
        return import_util.safe_column(self._metadata['supp_index_row'], col, idx=idx)

    def _index_label_col(self, col: str, idx: int | None = None) -> Any:
        """Read a keyword of the primary index's own label.

        Parameters:
            col: The label keyword to read.
            idx: Which element to read from a keyword holding a sequence.

        Returns:
            The value, as described in `ObsBase._index_col`. A label keyword describes
            the whole index file, so it is the same for every observation in it.
        """
        assert self._metadata is not None
        return import_util.safe_column(self._metadata['index_label'], col, idx=idx)

    def _supp_index_label_col(self, col: str, idx: int | None = None) -> Any:
        """Read a keyword of the supplemental index's own label.

        Parameters:
            col: The label keyword to read.
            idx: Which element to read from a keyword holding a sequence.

        Returns:
            The value, as described in `ObsBase._index_label_col`.
        """
        assert self._metadata is not None
        return import_util.safe_column(self._metadata['supp_index_label'], col, idx=idx)

    def _ring_geo_index_col(
        self,
        col: str,
        col2: str | None = None,
        col3: str | None = None,
        idx: int | None = None,
        missing_ok: bool = False,
    ) -> FloatField:
        """Read a column of the ring geometry summary row.

        Unlike the other index readers this one declares a float, because every column
        of a geometry summary file is one.

        Parameters:
            col: The column to read.
            col2: A second spelling to try if `col` is absent, which is how a single
                accessor serves both the older geometry files, where a gridless quantity
                has one column, and the newer ones, where it has a minimum and a
                maximum.
            col3: A third spelling, tried after `col2`.
            idx: Which element to read from a column holding a sequence.
            missing_ok: True to return None quietly when none of the spellings is
                present, rather than logging an error.

        Returns:
            The value, or None if this bundle has no ring geometry, this observation has
            no row in it, or the column is absent or masked as missing.
        """
        # Look up col; if missing try col2 instead. This supports both old and
        # new ring geometry metadata files, where the old ones have a single
        # value for gridless columns (e.g. ring_center_distance) while the
        # new ones have both minimum and maximum fields.

        # ring_geo is an optional index file so we allow it to be missing
        assert self._metadata is not None
        if 'ring_geo_row' not in self._metadata or self._metadata['ring_geo_row'] is None:
            return None
        if (
            col not in self._metadata['ring_geo_row']
            and (col2 is None or col2 not in self._metadata['ring_geo_row'])
            and (col3 is None or col3 not in self._metadata['ring_geo_row'])
        ):
            if not missing_ok:
                if col2 is None:
                    self._log_nonrepeating_error(f'Column "{col}" not found in ring_geo')
                else:
                    self._log_nonrepeating_error(
                        f'Columns "{col}" or "{col2}" not found in ring_geo'
                    )
            return None
        ret: FloatField = import_util.safe_column(self._metadata['ring_geo_row'], col, idx=idx)
        if ret is None and col2 is not None:
            ret = import_util.safe_column(self._metadata['ring_geo_row'], col2, idx=idx)
        if ret is None and col3 is not None:
            ret = import_util.safe_column(self._metadata['ring_geo_row'], col3, idx=idx)
        return ret

    def _sky_geo_index_col(self, col: str, idx: int | None = None) -> FloatField:
        """Read a column of the sky geometry summary row.

        Parameters:
            col: The column to read.
            idx: Which element to read from a column holding a sequence.

        Returns:
            The value, or None if this bundle has no sky geometry, this observation has
            no row in it, or the column is absent or masked as missing.
        """
        assert self._metadata is not None
        if 'sky_geo_row' not in self._metadata or self._metadata['sky_geo_row'] is None:
            return None
        ret: FloatField = import_util.safe_column(self._metadata['sky_geo_row'], col, idx=idx)
        return ret

    def _surface_geo_index_col(
        self,
        col: str,
        col2: str | None = None,
        col3: str | None = None,
        idx: int | None = None,
        missing_ok: bool = False,
    ) -> FloatField:
        """Read a column of the surface geometry summary row for the current target.

        Parameters:
            col: The column to read.
            col2: A second spelling to try if `col` is absent, for the same reason as in
                `ObsBase._ring_geo_index_col`.
            col3: A third spelling, tried after `col2`.
            idx: Which element to read from a column holding a sequence.
            missing_ok: True to return None quietly when none of the spellings is
                present, rather than logging an error.

        Returns:
            The value, or None if this bundle has no surface geometry, this observation
            has no row in it, or the column is absent or masked as missing.
        """
        # Look up col; if missing try col2 instead. This supports both old and
        # new surface geometry metadata files, where the old ones have a single
        # value for gridless columns (e.g. center_distance) while the
        # new ones have both minimum and maximum fields.

        # surface_geo is an optional index file so we allow it to be missing
        assert self._metadata is not None
        if 'surface_geo_row' not in self._metadata or self._metadata['surface_geo_row'] is None:
            return None
        if (
            col not in self._metadata['surface_geo_row']
            and (col2 is None or col2 not in self._metadata['surface_geo_row'])
            and (col3 is None or col3 not in self._metadata['surface_geo_row'])
        ):
            if not missing_ok:
                if col2 is None:
                    self._log_nonrepeating_error(f'Column "{col}" not found in surface_geo')
                else:
                    self._log_nonrepeating_error(
                        f'Columns "{col}" or "{col2}" not found in surface_geo'
                    )
            return None
        ret: FloatField = import_util.safe_column(self._metadata['surface_geo_row'], col, idx=idx)
        if ret is None and col2 is not None:
            ret = import_util.safe_column(self._metadata['surface_geo_row'], col2, idx=idx)
        if ret is None and col3 is not None:
            ret = import_util.safe_column(self._metadata['surface_geo_row'], col3, idx=idx)
        return ret

    def _col_in_index(self, col: str) -> bool:
        """Whether the primary index row carries a column.

        Parameters:
            col: The column to look for.
        """
        assert self._metadata is not None
        return col in self._metadata['index_row']

    def _col_in_supp_index(self, col: str) -> bool:
        """Whether the supplemental index row carries a column.

        Parameters:
            col: The column to look for.
        """
        assert self._metadata is not None
        return col in self._metadata['supp_index_row']

    def _col_in_some_index(self, col: str) -> str | None:
        """Find which index row carries a column.

        Parameters:
            col: The column to look for.

        Returns:
            The metadata key of the index that has it, or None if neither does. The
            supplemental index wins when both carry the column, which is what decides
            the value for COCIRS_[01]xxx.
        """
        # Figure out if col is in the supplemental index or normal index
        # and return the index name as appropriate. If not found anywhere,
        # return None. Very important: We prioritize the supplemental index
        # if the field exists in both. This makes a difference for
        # COCIRS_[01]xxx.
        assert self._metadata is not None
        for index in ['supp_index_row', 'index_row']:
            if index in self._metadata and col in self._metadata[index]:
                return index
        return None

    def _col_in_some_index_or_label(self, col: str) -> str | None:
        """Find which index row or index label carries a column.

        Parameters:
            col: The column or label keyword to look for.

        Returns:
            The metadata key of the index or label that has it, or None if none does.
            The order of preference is the same as in `ObsBase._col_in_some_index`, with
            the two labels tried after both rows.
        """
        # Figure out if col is in the supplemental index or normal index
        # or one of the associated label files and return the index name
        # as appropriate. If not found anywhere, return None.
        assert self._metadata is not None
        for index in ['supp_index_row', 'index_row', 'supp_index_label', 'index_label']:
            if (
                index in self._metadata
                and self._metadata[index] is not None
                and col in self._metadata[index]
            ):
                return index
        return None

    def _some_index_col(self, col: str, idx: int | None = None) -> Any:
        """Read a column from whichever index row carries it.

        Parameters:
            col: The column to read.
            idx: Which element to read from a column holding a sequence.

        Returns:
            The value, as described in `ObsBase._index_col`, or None if no index carries
            the column, which is logged as an error.
        """
        index = self._col_in_some_index(col)
        if index is None:
            self._log_nonrepeating_error(f'Column "{col}" not found in supp_index or index')
            return None
        assert self._metadata is not None
        return import_util.safe_column(self._metadata[index], col, idx=idx)

    def _some_index_or_label_col(self, col: str, idx: int | None = None) -> Any:
        """Read a column from whichever index row or index label carries it.

        Parameters:
            col: The column or label keyword to read.
            idx: Which element to read from a column holding a sequence.

        Returns:
            The value, as described in `ObsBase._index_col`, or None if nothing carries
            the column, which is logged as an error.
        """
        index = self._col_in_some_index_or_label(col)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{col}" not found in supp_index or index or their labels'
            )
            return None
        assert self._metadata is not None
        return import_util.safe_column(self._metadata[index], col, idx=idx)

    ### Utility functions useful for subclasses ###

    def _get_target_info(self, target_name: str | None) -> tuple[str | None, TargetInfo | None]:
        """Look a target name up, applying this pipeline's spelling corrections first.

        Parameters:
            target_name: The name as the PDS label spells it, in any case.

        Returns:
            The corrected name and its `TargetInfo`, or ``(None, None)`` if the name is
            one `opus_import.config_targets.TARGET_NAME_INFO` does not describe, which
            is reported through the run's unknown-target-name log. Under
            ``--import-ignore-errors`` an unknown name becomes ``'OTHER'`` and its
            entry, so that the observation still imports.
        """
        # Given a target_name, map the name as necessary and return the
        # target_class tuple (planet_id, target_class, pretty name).
        # Example: ('JUP', 'IRR_SAT', 'Callirrhoe')
        if target_name is None:
            return None, None
        target_name = target_name.upper()
        if target_name in config_targets.TARGET_NAME_MAPPING:
            target_name = config_targets.TARGET_NAME_MAPPING[target_name]
        if target_name not in config_targets.TARGET_NAME_INFO:
            self._log_unknown_target_name(target_name)
            if self._ignore_errors:
                return 'OTHER', config_targets.TARGET_NAME_INFO['OTHER']
            return None, None
        return target_name, config_targets.TARGET_NAME_INFO[target_name]

    def _get_planet_group_info(self, target_name: str | None) -> dict[str, str]:
        """Return how a target's planet group is shown in the search form.

        Parameters:
            target_name: A corrected target name, as `ObsBase._get_target_info` returns.

        Returns:
            The `opus_import.config_targets.PLANET_GROUP_MAPPING` entry, which carries
            the group's label and its sort key. A target with no planet, or one this
            pipeline does not describe, is grouped under ``OTHER``.
        """
        # Return the planet group info for a passed in target_name
        if target_name not in config_targets.TARGET_NAME_INFO:
            planet_id: str | None = 'OTHER'
        else:
            assert target_name is not None
            planet_id = config_targets.TARGET_NAME_INFO[target_name][0]
            if planet_id is None:
                planet_id = 'OTHER'
        return config_targets.PLANET_GROUP_MAPPING[planet_id]

    def _create_mult(
        self,
        col_val: str | int | float | None,
        disp_name: str | None = None,
        disp: str = 'Y',
        disp_order: int | str | None = None,
        grouping: str | None = None,
        group_disp_order: str | None = None,
        tooltip: str | None = None,
        aliases: list[str] | None = None,
    ) -> MultField:
        """Build the value a group column's field method returns.

        A group column stores an index into a ``mult_`` table rather than the value
        itself, and that table also carries how the web application presents the value.
        Everything but `col_val` is presentation, and every one of those may be left out
        -- `opus_import.steps.do_import_mult.update_mult_table` derives a label and a
        sort order from the value when none is given.

        Parameters:
            col_val: The value this row of the mult table stands for.
            disp_name: The label to show, or None to derive one.
            disp: ``'Y'`` to offer the value in the search form, ``'N'`` to hide it.
            disp_order: The sort key, or None to derive one.
            grouping: The group the value belongs to in the search form.
            group_disp_order: The group's sort key, or None to sort groups by name.
            tooltip: Kept in the result and read by nothing; see
                `opus_import.obs.field_types.MultField`.
            aliases: Other spellings a search should accept, stored as JSON. No obs
                class passes any.

        Returns:
            The `opus_import.obs.field_types.MultField` for this value.
        """
        data_dict: MultField = {
            'col_val': col_val,
            'disp': disp,
            'disp_name': disp_name,
            'disp_order': disp_order,
            'grouping': grouping,
            'group_disp_order': group_disp_order,
            'tooltip': tooltip,
            'aliases': json.dumps(aliases) if aliases else None,
        }
        # For testing purpose: uncomment the following code to hide the Dark field
        # under "Other" in target widget and also store aliases for the field.
        # if col_val == 'DARK':
        #     data_dict['disp'] = 'N'
        #     aliases_list = ['dark_1', 'dark_2', 'dark_3']
        #     data_dict['aliases'] = json.dumps(aliases_list)
        return data_dict

    def _create_mult_keep_case(
        self,
        col_val: str | None,
        disp: str = 'Y',
        disp_order: int | str | None = None,
        grouping: str | None = None,
        group_disp_order: str | None = None,
        tooltip: str | None = None,
        aliases: list[str] | None = None,
    ) -> MultField:
        """Build a group column's value, showing it exactly as it is spelled.

        `ObsBase._create_mult` leaves the label to be derived, and the derivation
        title-cases it. This passes the value through as the label instead, which is
        what a value whose capitalization carries meaning -- a filter name, an
        observation name -- needs.

        Parameters:
            col_val: The value, which is also the label.
            disp: As in `ObsBase._create_mult`.
            disp_order: As in `ObsBase._create_mult`.
            grouping: As in `ObsBase._create_mult`.
            group_disp_order: As in `ObsBase._create_mult`.
            tooltip: As in `ObsBase._create_mult`.
            aliases: As in `ObsBase._create_mult`.

        Returns:
            The `opus_import.obs.field_types.MultField` for this value.
        """
        return self._create_mult(
            col_val=col_val,
            disp_name=col_val,
            disp=disp,
            disp_order=disp_order,
            grouping=grouping,
            group_disp_order=group_disp_order,
            tooltip=tooltip,
            aliases=aliases,
        )

    # Helpers for time fields

    def _time_helper(self, index: str, column: str, missing_index_ok: bool = False) -> FloatField:
        """Read and convert a time from one of the indexes.

        Parameters:
            index: The metadata key of the index or label to read.
            column: The column holding the time, as an ISO string.
            missing_index_ok: True to return None quietly when that index is absent,
                rather than failing.

        Returns:
            The time in seconds TAI, or None if the column is missing. An unparsable
            time is logged as an error and returns None too.
        """
        # Read and convert a time, which can exist in various indexes or
        # columns.
        assert self._metadata is not None
        if missing_index_ok and (index not in self._metadata or self._metadata[index] is None):
            return None
        the_time = import_util.safe_column(self._metadata[index], column)
        if the_time is None:
            return None

        try:
            time_sec: float = import_util.cached_tai_from_iso(the_time)
        except Exception as e:
            self._log_nonrepeating_error(f'Bad {column} format "{the_time}": {e}')
            return None

        return time_sec

    def _time2_helper(
        self, index: str, start_time_sec: FloatField, column: str, missing_index_ok: bool = False
    ) -> FloatField:
        """Read and convert a stop time, holding it at or after the start time.

        Parameters:
            index: The metadata key of the index or label to read.
            start_time_sec: The observation's start time, in seconds TAI.
            column: The column holding the time, as an ISO string.
            missing_index_ok: True to return None quietly when that index is absent,
                rather than failing.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable, as
            in `ObsBase._time_helper`. A stop time earlier than `start_time_sec` is
            logged as a warning and replaced by the start time, since the pair is
            otherwise an unsearchable range.
        """
        # Read and convert the ending time, which can exist in various indexes or
        # columns. Compare it to the starting time to make sure they're in the proper
        # order.
        assert self._metadata is not None
        if missing_index_ok and (index not in self._metadata or self._metadata[index] is None):
            return None
        index_row = self._metadata[index]
        stop_time = import_util.safe_column(index_row, column)
        if stop_time is None:
            return None

        try:
            stop_time_sec: float = import_util.cached_tai_from_iso(stop_time)
        except Exception as e:
            self._log_nonrepeating_error(f'Bad {column} format "{stop_time}": {e}')
            return None

        if start_time_sec is not None and stop_time_sec < start_time_sec:
            self._log_nonrepeating_warning(
                f'{column} start and end ({stop_time}) '
                + 'are in the wrong order - setting to start time'
            )
            stop_time_sec = start_time_sec

        return stop_time_sec

    # Helper for spacecraft clock fields

    def _parse_sclk(
        self,
        parse_func: Callable[[str], float],
        sclk: str,
        mission_name: str,
        log_func: Callable[[str], None] | None = None,
    ) -> FloatField:
        """Parse a spacecraft clock count, reporting a bad one instead of raising.

        Every mission's spacecraft_clock_count field function needs the same
        error handling, so the mission common classes wrap this in a
        `_parse_<mission>_sclk` helper and the field functions call that.

        Parameters:
            parse_func: The opus_support parser for this mission's SCLK format.
            sclk: The SCLK string to parse.
            mission_name: The mission's display name, for the error message.
            log_func: How to report a bad SCLK; defaults to
                `ObsBase._log_nonrepeating_error`.

        Returns:
            The converted SCLK, or None if it could not be parsed. None is unambiguous:
            the opus_support parsers all return a number or raise.
        """
        try:
            return parse_func(sclk)
        except Exception as e:
            if log_func is None:
                log_func = self._log_nonrepeating_error
            log_func(f'Unable to parse {mission_name} SCLK "{sclk}": {e}')
            return None

    ### Error logging ###

    def _log_unknown_target_name(self, target_name: str) -> None:
        """Record a target name this pipeline does not describe.

        Parameters:
            target_name: The name, already corrected for spelling.
        """
        self._ctx.log.unknown_target_name(target_name)

    def _log_warning(self, *args: Any, **kwargs: Any) -> None:
        """Log a warning against the current bundle.

        Parameters:
            args: Passed through to `opus_import.context.ImportLog.warning`.
            kwargs: Passed through as well.
        """
        self._ctx.log.warning(*args, **kwargs)

    def _log_nonrepeating_warning(self, *args: Any, **kwargs: Any) -> None:
        """Log a warning at most once per bundle, however many rows produce it.

        Parameters:
            args: Passed through to
                `opus_import.context.ImportLog.nonrepeating_warning`.
            kwargs: Passed through as well.
        """
        self._ctx.log.nonrepeating_warning(*args, **kwargs)

    def _log_nonrepeating_error(self, *args: Any, **kwargs: Any) -> None:
        """Log an error at most once per bundle, however many rows produce it.

        Parameters:
            args: Passed through to `opus_import.context.ImportLog.nonrepeating_error`.
            kwargs: Passed through as well.
        """
        self._ctx.log.nonrepeating_error(*args, **kwargs)
