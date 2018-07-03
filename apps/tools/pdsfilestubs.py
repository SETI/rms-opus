################################################################################
# pdsfilestubs.py
#
# Stubs for pdsfile api to replace the
#        models: Image, FileSizes, Files
################################################################################
import pdsfile
from tools.app_utils import iter_flatten
from settings import IMAGE_HTTP_PATH

import logging
log = logging.getLogger(__name__)

def get_base_path(opus_id):
    """Return the base path of the images for opus_id."""

def get_image_details(opus_id, size='thumb'):
    """Return the url, size of the requested image."""
    # size = 'small', 'med', 'full', 'thumb'
    #pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
    return 'VGISS_6101/DATA/C32500XX/C3250013_thumb.jpg', 1300

def get_image_links(opus_id_list, size):
    """Return the set of fully qualified image links (thumb, small, med, full) for list of page_ids."""

    # just to get past not having shelv files for now..., pixels
    img_sizes = {}
    img_sizes['thumb'] = 100
    img_sizes['small'] = 256
    img_sizes['med'] = 512
    img_sizes['large'] = 1024

    if isinstance(opus_id_list,type(basestring)):
        opus_id_list = [opus_id_list]

    image_links = []
    for opus_id in opus_id_list:
        image = {'opus_id': opus_id}
        pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        preview = pdsf.viewset.for_frame(img_sizes[size])
        image['url'] = IMAGE_HTTP_PATH + preview.url
        image['alt_text'] = preview.alt
        image_links.append(image)

    return image_links
