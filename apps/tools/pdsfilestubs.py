################################################################################
# pdsfilestubs.py
#
# Stubs for pdsfile api to replace the
#        models: Image, FileSizes, Files
################################################################################
import pdsfile

import logging
log = logging.getLogger(__name__)

def get_base_path(opus_id):
    """Return the base path of the images for opus_id."""

def get_image_details(opus_id, size='thumb'):
    """Return the url, size of the requested image."""
    # size = 'small', 'med', 'full', 'thumb'
    #pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
    return 'VGISS_6101/DATA/C32500XX/C3250013_thumb.jpg', 1300

def get_image_links(opus_id_list):
    """Return the set of fully qualified image links (thumb, small, med, full) for list of page_ids."""

    if isinstance(opus_id_list,type(basestring)):
        opus_id_list = [opus_id_list]

    for opus_id in opus_id_list:
        pdsf = pdsfile.PdsFile.from_opus_id(opus_id)
        products = pdsf.opus_products()
        for (opus_type, list_of_sublists) in products.items():
            if opus_type.lower().find("image") >= 0:
                log.error(sublists)

    # just placeholder so it doesn't matter what is passed in at moment
    page_ids = [u'S_IMG_VG1_ISS_3250013_N', u'S_IMG_VG1_ISS_3250015_N', u'S_IMG_VG1_ISS_3250017_N']
    stubpath = 'VGISS_6XXX/VGISS_6101/DATA/C32500XX/C'

    image_links = []
    for opus_id in page_ids:
        base = stubpath + opus_id.split('_')[-2]
        image = {}
        image['opus_id'] = opus_id
        image['thumb'] = base + "_thumb.jpg"
        image['instrument_id'] = "VGISS"	       # get from api
        image['small'] = base + "_small.jpg"
        image['med'] = base + "_med.jpg"
        image['full'] =	base + "_full.jpg"
        image['volume_id'] = stubpath.split("/")[0]	# get from api
        image['size_thumb'] = 1309	# get from api
        image['size_small'] = 2378	# get from api
        image['size_med'] = 5856    # get from api
        image['size_full'] = 20078  # get from api
        image_links.append(image)

    return image_links
