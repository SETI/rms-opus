################################################################################
#
# tools/file_utils.py
#
# This file contains utilities that interact with the obs_files table.
#
################################################################################

"""Lookups against the `obs_files` table, which lists the files of each observation.

Every function here starts from one or more opus_ids and returns files that belong
to them: all of an observation's PDS products, its preview images, or the browse
products the Detail tab displays. Nothing here writes to the database.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pdsfile.pdsviewable
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from opus_app.apps.search.models import ObsGeneral
from opus_app.apps.tools import sql_builder

if TYPE_CHECKING:
    from collections.abc import Collection

log = logging.getLogger(__name__)


def get_pds_products(
    opus_id_list: str | list[str] | tuple[str, ...],
    loc_type: str = 'url',
    product_types: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, dict[str, dict[tuple[str, int, str, str], list[Any]]]]:
    """Return all PDS products for a given opus_id(s) organized by version.

    Parameters:
        opus_id_list: One opus_id, or a list or tuple of them.
        loc_type: `'url'` for each file's full URL, `'path'` for its path on the
            local disk, or `'raw'` for a dict holding the URL, the path, the
            checksum and the file's other `obs_files` columns.
        product_types: One product type, a comma-separated string of them, or a
            list or tuple of them. A string is lowercased before it is split; a
            list or tuple is used as it is given. `'all'` on its own asks for every
            product type, which is also what omitting the argument does. A product
            type is a `short_name` from `obs_files`, optionally followed by `@` and
            a version name, where `@Current` (in any casing) means the current
            version and `@all` means every version. A product type given without
            `@` matches the current version only.

    Returns:
        A dict with one entry per opus_id given, in the order they were given; an
        opus_id with no matching file maps to an empty dict. Each entry maps a
        version name to a dict keyed by
        `(category, sort_order, short_name, full_name)`, whose value is the list of
        that product type's files. What each file is reported as is chosen by
        `loc_type`: a URL, a path, or a dict. Versions and product types appear in
        the order the query returns them, which is version number descending and
        then the product's sort order.
    """
    assert loc_type in ('path', 'url', 'raw'), loc_type
    assert opus_id_list is not None

    if product_types is None:
        product_types = ['all']

    if not isinstance(product_types, (list, tuple)):
        product_types = product_types.lower().split(',')

    if not isinstance(opus_id_list, (list, tuple)):
        opus_id_list = [opus_id_list]

    assert len(opus_id_list) > 0
    assert len(product_types) > 0

    results: dict[
        str, dict[str, dict[tuple[str, int, str, str], list[Any]]]
    ] = {}  # Dict of opus_ids

    cursor = connection.cursor()

    def obs_files_column(name: str) -> sql_builder.Expr:
        """Return the named column of the `obs_files` table."""
        return sql_builder.column(name, 'obs_files')

    select = sql_builder.Select()
    for column_name in (
        'opus_id',
        'version_name',
        'category',
        'sort_order',
        'short_name',
        'full_name',
        'size',
        'pds_version',
    ):
        select.add_column(obs_files_column(column_name))
    if loc_type == 'path' or loc_type == 'raw':
        select.add_column(obs_files_column('logical_path'))
    if loc_type == 'url' or loc_type == 'raw':
        select.add_column(obs_files_column('url'))
    if loc_type == 'raw':
        select.add_column(obs_files_column('checksum'))

    select.add_from('obs_files')
    if product_types != ['all']:
        # Because we didn't store @version in the database, when multiple versions (or
        # product types) are passed in, we need to query the database by both short name
        # and version name for each product type in the product_types list. The query
        # condition will be something like:
        # (obs_files.short_name='coiss_calib' AND obs_files.version_name='Current') OR
        # (obs_files.short_name='coiss_calib' AND obs_files.version_name='1') OR
        # (obs_files.short_name='coiss_raw' AND obs_files.version_name='Current') OR
        # ...
        product_type_conditions = []
        for p in product_types:
            # Check and see if the product type has a version specified (look for '@')
            if '@' in p:
                prod_type, _, version = p.partition('@')
                if version.lower() == 'current':
                    version = 'Current'
                condition = sql_builder.binary_op(
                    obs_files_column('short_name'), '=', sql_builder.value(prod_type)
                )
                if version.lower() != 'all':
                    condition = sql_builder.join_exprs(
                        [
                            condition,
                            sql_builder.binary_op(
                                obs_files_column('version_name'), '=', sql_builder.value(version)
                            ),
                        ],
                        'AND',
                    )
            else:
                # When there is no modifier "@" in types, we will display "Current"
                # version of the files. This will match the behavior of api/download
                condition = sql_builder.join_exprs(
                    [
                        sql_builder.binary_op(
                            obs_files_column('short_name'), '=', sql_builder.value(p)
                        ),
                        sql_builder.binary_op(
                            obs_files_column('version_name'), '=', sql_builder.value('Current')
                        ),
                    ],
                    'AND',
                )
            product_type_conditions.append(sql_builder.parenthesize(condition))
        select.add_where(
            sql_builder.parenthesize(sql_builder.join_exprs(product_type_conditions, 'OR'))
        )
    select.add_where(sql_builder.in_sequence(obs_files_column('opus_id'), opus_id_list))
    select.add_order_by(obs_files_column('opus_id'))
    select.add_order_by(obs_files_column('version_number'), descending=True)
    select.add_order_by(obs_files_column('sort_order'))
    select.add_order_by(obs_files_column('product_order'))
    # Keep individual files in original order
    select.add_order_by(obs_files_column('id'))

    sql, values = select.build()
    log.debug('get_pds_products SQL: %r %r', sql, values)
    cursor.execute(sql, values)

    # We do this here so if there aren't any products, there's still an empty
    # dictionary returned
    for opus_id in opus_id_list:
        results[opus_id] = {}  # Dict of versions

    for row in cursor:
        path: str | None = None
        url: str | None = None
        if loc_type == 'path':
            (
                opus_id,
                version_name,
                category,
                sort_order,
                short_name,
                full_name,
                size,
                pds_version,
                path,
            ) = row
        elif loc_type == 'url':
            (
                opus_id,
                version_name,
                category,
                sort_order,
                short_name,
                full_name,
                size,
                pds_version,
                url,
            ) = row
        else:
            (
                opus_id,
                version_name,
                category,
                sort_order,
                short_name,
                full_name,
                size,
                pds_version,
                path,
                url,
                checksum,
            ) = row

        # sort_order is in the format CASISSxxx where xxx is the original numeric
        # sort order
        sort_order = int(sort_order[6:])
        if version_name not in results[opus_id]:
            results[opus_id][version_name] = {}
        product_type = (category, sort_order, short_name, full_name)
        if product_type not in results[opus_id][version_name]:
            results[opus_id][version_name][product_type] = []

        if path:
            if pds_version == 3:
                path = settings.PDS3_DATA_DIR.rstrip('/') + '/' + path
            else:
                path = settings.PDS4_DATA_DIR.rstrip('/') + '/' + path
        if url:
            url = settings.PRODUCT_HTTP_PATH.rstrip('/') + '/' + url

        # What a file is reported as is chosen by loc_type, so this holds a path, a
        # URL, or the whole record depending on which branch below runs.
        res: str | dict[str, Any] | None
        if loc_type == 'path':
            res = path
        elif loc_type == 'url':
            res = url
        else:
            res = {
                'path': path,
                'url': url,
                'checksum': checksum,
                'category': category,
                'version_name': version_name,
                'full_name': full_name,
                'short_name': short_name,
                'size': size,
                'pds_version': pds_version,
            }
        if res not in results[opus_id][version_name][product_type]:
            results[opus_id][version_name][product_type].append(res)

    return results


def get_pds_preview_images(
    opus_id_list: str | list[str] | tuple[str, ...] | None,
    preview_jsons: list[Any] | None,
    sizes: str | Collection[str] | None = None,
    ignore_missing: bool = False,
) -> list[dict[str, Any]]:
    """Given a list of opus_ids, return a list of image info for each size.

    Parameters:
        opus_id_list: One opus_id, or a list or tuple of them; nothing at all is
            also accepted and gives an empty list back.
        preview_jsons: The `obs_general.preview_images` entry for each opus_id, in
            the same order, or nothing at all to look each one up.
        sizes: One image size, or a collection of them, out of `'thumb'`,
            `'small'`, `'med'` and `'full'`; all four when omitted.
        ignore_missing: When true, an observation with no preview image is reported
            without that size's entries instead of with the placeholder ones.

    Returns:
        One dict per opus_id, each holding `'opus_id'` and, for every size asked
        for, that size's `_url`, `_alt_text`, `_size_bytes`, `_width` and `_height`
        entries. An observation with no preview image gets the not-found thumbnail
        and zeroes, unless `ignore_missing` asked for those entries to be left out.

    Raises:
        KeyError: If a size is not one of the four listed above.
    """
    if opus_id_list:
        if not isinstance(opus_id_list, (list, tuple)):
            opus_id_list = [opus_id_list]
    else:
        opus_id_list = []

    if sizes is None:
        sizes = settings.PREVIEW_SIZE_TO_PDS_TYPE.keys()
    elif not isinstance(sizes, (list, tuple)):
        # A single size name reaches here. mypy cannot tell that apart from the
        # collection the branch above puts in this same variable.
        sizes = [sizes]  # type: ignore[list-item]

    product_types: list[str] = []
    for size in sizes:
        product_types += settings.PREVIEW_SIZE_TO_PDS_TYPE[size]

    image_list = []
    for idx in range(len(opus_id_list)):
        opus_id = opus_id_list[idx]
        preview_json = None
        if preview_jsons:
            preview_json = preview_jsons[idx]
        else:
            try:
                preview_json = ObsGeneral.objects.get(opus_id=opus_id).preview_images
            except ObjectDoesNotExist:  # pragma: no cover - import error
                log.error(
                    'get_pds_preview_images: Failed to find opus_id "%r" ' + 'in obs_general',
                    opus_id,
                )
        viewset = None
        if preview_json:  # pragma: no cover - import error
            viewset = pdsfile.pdsviewable.PdsViewSet.from_dict(preview_json)
        data: dict[str, Any] = {'opus_id': opus_id}
        for size in sizes:
            viewable = None
            if viewset:
                if size == 'thumb':
                    viewable = viewset.thumbnail
                elif size == 'small':
                    viewable = viewset.small
                elif size == 'med':
                    viewable = viewset.medium
                elif size == 'full':
                    viewable = viewset.full_size
                else:  # pragma: no cover - error catchall
                    log.error('Unknown image size "%r"', size)
            if not preview_json or not viewset:  # pragma: no cover
                # log.error('No preview image size %r found for '
                #           +'opus_id %r', size, opus_id)
                if ignore_missing:
                    continue
                url = settings.THUMBNAIL_NOT_FOUND
                alt_text = 'Not found'
                byte_size = 0
                width = 0
                height = 0
            else:
                # The only branch above that leaves viewable unset is the one for an
                # unrecognized size, and building product_types above already raised
                # KeyError for such a size before this loop was reached.
                assert viewable is not None
                url = settings.PRODUCT_HTTP_PATH.strip('/') + viewable.url
                if 'googleapis' in url:  # pragma: no cover
                    url = url.replace('/holdings', '/pds3-holdings')
                alt_text = viewable.alt
                byte_size = viewable.bytes
                width = viewable.width
                height = viewable.height
            data[size + '_url'] = url
            data[size + '_alt_text'] = alt_text
            data[size + '_size_bytes'] = byte_size
            data[size + '_width'] = width
            data[size + '_height'] = height
        image_list.append(data)

    return image_list


def get_displayed_browse_products(
    opus_id: str, version_name: str = 'Current'
) -> list[tuple[str, str]]:
    """Return the browse product URLs to display on an observation's Detail tab.

    Parameters:
        opus_id: The observation whose browse products are wanted.
        version_name: The product version to take them from.

    Returns:
        One `(medium url, full url)` pair per browse product that has both sizes,
        or a single pair of the not-found thumbnail when the observation has no
        browse product in that version.
    """
    browse_products = get_pds_products(opus_id, product_types=settings.DISPLAYED_BROWSE_PRODUCTS)

    # `.get` falls back to an empty list rather than an empty dict, which the
    # emptiness test below accepts and returns for before anything treats it as a
    # dict, so the declaration describes every value that reaches the loop.
    selected_browse_products: dict[tuple[str, int, str, str], list[Any]] = browse_products[
        opus_id
    ].get(version_name, [])  # type: ignore[arg-type]
    # When there is no preview image, we return settings.THUMBNAIL_NOT_FOUND
    if len(selected_browse_products) == 0:  # pragma: no cover - thumbnails not available
        return [(settings.THUMBNAIL_NOT_FOUND, settings.THUMBNAIL_NOT_FOUND)]
    res = []
    # One opus id could have multiple previews, for example:
    # co-rss-occ-2008-039-rev058c-x43-i
    # co-uvis-occ-2005-232-alpsco-i
    # Get paired medium and full browse urls in res (medium url, full url)
    disp_prod_dict: dict[str, str] = {}
    for p in selected_browse_products:
        for browse_url in selected_browse_products[p]:
            if '_med.' in browse_url:
                basename, _, _ = browse_url.partition('_med.')
                if basename in disp_prod_dict:  # pragma: no cover -
                    # The order of browse products is usually medium,full
                    # so this never gets triggered, since it would require
                    # the full image to come first.
                    res.append((browse_url, disp_prod_dict[basename]))
                    continue
            else:  # '_full.' in browse_url
                basename, _, _ = browse_url.partition('_full.')
                if basename in disp_prod_dict:  # pragma: no cover - see above
                    res.append((disp_prod_dict[basename], browse_url))
                    continue
            disp_prod_dict[basename] = browse_url

    return res
