"""The ``obs_preview`` column: the preview images ``rms-pdsfile`` knows for an observation.

One module per OPUS table, mixed into every obs class that fills the table. Every
observation has one row here, beside its ``obs_general`` row, holding its view set as
JSON.
"""

import json
import os

from pdsfile.pdsviewable import PdsViewSet

from opus_import.obs.field_types import StrField
from opus_import.obs.obs_base import ObsBase


class ObsPreview(ObsBase):
    """The ``obs_preview`` column, which every observation has.

    Its ``field_obs_*`` method fills the schema column its name ends in, declaring the
    type `opus_import.obs.field_types` gives that column.
    """

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_preview_preview_images(self) -> StrField:
        """Return the observation's preview images as JSON text.

        The images are the view set ``rms-pdsfile`` gives the observation's primary
        filespec, encoded as ``PdsViewSet.to_dict`` encodes it: an object whose
        ``viewables`` list holds, for each image, its ``url``, ``width``, ``height`` and
        ``bytes``, and its ``name`` when it has one, with a ``priority`` when that is not
        zero. Unless ``--ignore-missing-images`` is given, a warning is logged for each of
        the thumbnail, small, medium and full-size images the set lacks.

        An observation without a primary filespec gets ``{"viewables": []}``, with a
        warning. When ``rms-pdsfile`` gives no view set or an empty one, or raises
        ``ValueError`` or ``OSError`` asking for it (each logged as a warning), the result
        is ``{"viewables": []}``, with a warning unless ``--ignore-missing-images`` is
        given, or, with ``--fake-images``, four made-up images. Each is named after the
        product's logical path without its extension, under ``holdings/``, with
        ``volumes`` replaced by ``previews`` (for a CIRS product by ``diagrams``, and
        ``DATA/APODSPEC/SPEC`` by ``BROWSE/TARGETS/IMG``), suffixed ``_thumb``,
        ``_small``, ``_med`` and ``_full`` (the last also named ``full``), as ``.png`` for
        a VIMS or UVIS product and ``.jpg`` otherwise; they are 100, 256, 512 and 1024
        pixels square.

        Returns:
            The view set as JSON text.
        """
        ### XXX Review this
        filespec = self.primary_filespec
        if filespec is None:
            self._log_nonrepeating_warning('No preview images: this observation has no filespec')
            return json.dumps({'viewables': []})
        pdsf = self._pdsfile_from_filespec(filespec)

        try:
            viewset = pdsf.viewset
        except ValueError as e:
            self._log_nonrepeating_warning(f'ViewSet threw ValueError for "{filespec}": {e}')
            viewset = None
        except OSError as e:
            self._log_nonrepeating_warning(f'ViewSet threw IOError for "{filespec}": {e}')
            viewset = None

        # A miss comes back two different ways, and this branch has to reject both.
        # pdsfile answers a file that does not exist, and a directory whose candidate
        # children all decline, with None; everything else that fails gets an *empty*
        # `PdsViewSet`, which is falsy but is not None -- and whose `thumbnail` raises
        # IndexError rather than returning nothing. So the test is for a real set that
        # holds something: the isinstance is what leaves a `PdsViewSet` in the type
        # instead of a bool, and the truthiness is what keeps the empty one out.
        if isinstance(viewset, PdsViewSet) and viewset:
            browse_data = viewset.to_dict()
            if not self._ctx.args.ignore_missing_images:
                if not viewset.thumbnail:
                    self._log_nonrepeating_warning(
                        f'Missing thumbnail browse/diagram image for "{filespec}"'
                    )
                if not viewset.small:
                    self._log_nonrepeating_warning(
                        f'Missing small browse/diagram image for "{filespec}"'
                    )
                if not viewset.medium:
                    self._log_nonrepeating_warning(
                        f'Missing medium browse/diagram image for "{filespec}"'
                    )
                if not viewset.full_size:
                    self._log_nonrepeating_warning(
                        f'Missing full_size browse/diagram image for "{filespec}"'
                    )
        else:
            if self._ctx.args.fake_images:
                base_path = os.path.splitext(pdsf.logical_path)[0]
                if base_path.find('CIRS') != -1:
                    base_path = base_path.replace('volumes', 'diagrams')
                    base_path = base_path.replace('DATA/APODSPEC/SPEC', 'BROWSE/TARGETS/IMG')
                else:
                    base_path = base_path.replace('volumes', 'previews')
                base_path = 'holdings/' + base_path
                ext = 'jpg'
                if (
                    base_path.find('VIMS') != -1  # XXX
                    or base_path.find('UVIS') != -1
                ):
                    ext = 'png'
                browse_data = {
                    'viewables': [
                        {
                            'url': base_path + '_thumb.' + ext,
                            'bytes': 500,
                            'width': 100,
                            'height': 100,
                        },
                        {
                            'url': base_path + '_small.' + ext,
                            'bytes': 1000,
                            'width': 256,
                            'height': 256,
                        },
                        {
                            'url': base_path + '_med.' + ext,
                            'bytes': 2000,
                            'width': 512,
                            'height': 512,
                        },
                        {
                            'url': base_path + '_full.' + ext,
                            'name': 'full',
                            'bytes': 4000,
                            'width': 1024,
                            'height': 1024,
                        },
                    ]
                }
            else:
                browse_data = {'viewables': []}
                if not self._ctx.args.ignore_missing_images:
                    self._log_nonrepeating_warning(
                        f'Missing all browse/diagram images for "{self.primary_filespec}"'
                    )

        ret = json.dumps(browse_data)
        return ret
