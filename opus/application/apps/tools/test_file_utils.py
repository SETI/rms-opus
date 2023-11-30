# tools/test_file_utils.py

import logging
from unittest import TestCase

from django.core.cache import cache
from tools.file_utils import get_pds_products

import settings

class fileUtilsTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        logging.disable(logging.ERROR)
        cache.clear()

    def tearDown(self):
        logging.disable(logging.NOTSET)


            ###############################################
            ######### get_pds_products UNIT TESTS #########
            ###############################################

    def test__get_pds_products_ib4v21gc_opusid_url(self):
        "[test_file_utils.py] get_pds_products: no versions opusid hst-11559-wfc3-ib4v21gc url"
        opus_id = 'hst-11559-wfc3-ib4v21gcq'
        ret = get_pds_products(opus_id)
        expected = {'hst-11559-wfc3-ib4v21gcq': {'Current': {('HST', 10, 'hst_text', 'FITS Header Text'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.ASC', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_RAW.TIF', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_RAW.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_FLT.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_DRZ.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 120, 'hst_documentation', 'Documentation'): ['https://opus.pds-rings.seti.org/holdings/documents/HSTIx_xxxx/WFC3-Instrument-Handbook-13.0.pdf', 'https://opus.pds-rings.seti.org/holdings/documents/HSTIx_xxxx/WFC3-Data-Handbook-4.0.pdf', 'https://opus.pds-rings.seti.org/holdings/documents/HSTIx_xxxx/FITS-Standard-4.0.pdf'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): ['https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.tab', 'https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.lbl'], ('metadata', 6, 'hstfiles_index', 'HST Files Associations Index'): ['https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.tab', 'https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_thumb.jpg'], ('browse', 20, 'browse_small', 'Browse Image (small)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_small.jpg'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_med.jpg'], ('browse', 40, 'browse_full', 'Browse Image (full)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_full.jpg']}}}
        print('Got:')
        print(ret)
        print('Expected:')
        print(expected)
        self.assertEqual(dict(ret), dict(expected))

    def test__get_pds_products_ib4v19r3q_opusid_url(self):
        "[test_file_utils.py] get_pds_products: versions opusid hst-11559-wfc3-ib4v19r3q url"
        opus_id = 'hst-11559-wfc3-ib4v19r3q'
        ret = get_pds_products(opus_id)
        expected = {'hst-11559-wfc3-ib4v19r3q': {'Current': {('HST', 10, 'hst_text', 'FITS Header Text'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.ASC', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.TIF', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_FLT.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_DRZ.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 120, 'hst_documentation', 'Documentation'): ['https://opus.pds-rings.seti.org/holdings/documents/HSTIx_xxxx/WFC3-Instrument-Handbook-13.0.pdf', 'https://opus.pds-rings.seti.org/holdings/documents/HSTIx_xxxx/WFC3-Data-Handbook-4.0.pdf', 'https://opus.pds-rings.seti.org/holdings/documents/HSTIx_xxxx/FITS-Standard-4.0.pdf'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): ['https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.tab', 'https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.lbl'], ('metadata', 6, 'hstfiles_index', 'HST Files Associations Index'): ['https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.tab', 'https://opus.pds-rings.seti.org/holdings/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_thumb.jpg'], ('browse', 20, 'browse_small', 'Browse Image (small)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_small.jpg'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_med.jpg'], ('browse', 40, 'browse_full', 'Browse Image (full)'): ['https://opus.pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_full.jpg']}, '1.1': {('HST', 10, 'hst_text', 'FITS Header Text'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.ASC', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.TIF', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_FLT.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_DRZ.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL']}, '1.0': {('HST', 10, 'hst_text', 'FITS Header Text'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.ASC', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.TIF', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_FLT.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): ['https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_DRZ.JPG', 'https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL']}}}
        print('Got:')
        print(ret)
        print('Expected:')
        print(expected)
        self.assertEqual(dict(ret), dict(expected))

    def test__get_pds_products_ib4v21gcq_opusid_path(self):
        "[test_file_utils.py] get_pds_products: no versions opusid hst-11559-wfc3-ib4v21gcq path"
        opus_id = 'hst-11559-wfc3-ib4v21gcq'
        ret = get_pds_products(opus_id, loc_type='path')
        expected = {'hst-11559-wfc3-ib4v21gcq': {'Current': {('HST', 10, 'hst_text', 'FITS Header Text'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.ASC', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_RAW.TIF', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_RAW.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_FLT.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_DRZ.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ.LBL'], ('HST', 120, 'hst_documentation', 'Documentation'): [settings.PDS_DATA_DIR+'/documents/HSTIx_xxxx/WFC3-Instrument-Handbook-13.0.pdf', settings.PDS_DATA_DIR+'/documents/HSTIx_xxxx/WFC3-Data-Handbook-4.0.pdf', settings.PDS_DATA_DIR+'/documents/HSTIx_xxxx/FITS-Standard-4.0.pdf'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): [settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.tab', settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.lbl'], ('metadata', 6, 'hstfiles_index', 'HST Files Associations Index'): [settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.tab', settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_thumb.jpg'], ('browse', 20, 'browse_small', 'Browse Image (small)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_small.jpg'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_med.jpg'], ('browse', 40, 'browse_full', 'Browse Image (full)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_21/IB4V21GCQ_full.jpg']}}}
        print('Got:')
        print(ret)
        print('Expected:')
        print(expected)
        self.assertEqual(dict(ret), dict(expected))

    def test__get_pds_products_ib4v19r3q_opusid_path(self):
        "[test_file_utils.py] get_pds_products: versions opusid hst-11559-wfc3-ib4v19r3q path"
        opus_id = 'hst-11559-wfc3-ib4v19r3q'
        ret = get_pds_products(opus_id, loc_type='path')
        expected = {'hst-11559-wfc3-ib4v19r3q': {'Current': {('HST', 10, 'hst_text', 'FITS Header Text'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.ASC', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.TIF', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_FLT.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_DRZ.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 120, 'hst_documentation', 'Documentation'): [settings.PDS_DATA_DIR+'/documents/HSTIx_xxxx/WFC3-Instrument-Handbook-13.0.pdf', settings.PDS_DATA_DIR+'/documents/HSTIx_xxxx/WFC3-Data-Handbook-4.0.pdf', settings.PDS_DATA_DIR+'/documents/HSTIx_xxxx/FITS-Standard-4.0.pdf'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): [settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.tab', settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_index.lbl'], ('metadata', 6, 'hstfiles_index', 'HST Files Associations Index'): [settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.tab', settings.PDS_DATA_DIR+'/metadata/HSTIx_xxxx/HSTI1_1559/HSTI1_1559_hstfiles.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_thumb.jpg'], ('browse', 20, 'browse_small', 'Browse Image (small)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_small.jpg'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_med.jpg'], ('browse', 40, 'browse_full', 'Browse Image (full)'): [settings.PDS_DATA_DIR+'/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_full.jpg']}, '1.1': {('HST', 10, 'hst_text', 'FITS Header Text'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.ASC', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.TIF', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_FLT.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_DRZ.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL']}, '1.0': {('HST', 10, 'hst_text', 'FITS Header Text'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.ASC', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 20, 'hst_tiff', 'Raw Data Preview (lossless)'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.TIF', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 30, 'hst_raw', 'Raw Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_RAW.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 40, 'hst_calib', 'Calibrated Data Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_FLT.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL'], ('HST', 70, 'hst_drizzled', 'Calibrated Geometrically Corrected Preview'): [settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q_DRZ.JPG', settings.PDS_DATA_DIR+'/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19R3Q.LBL']}}}
        print('Got:')
        print(ret)
        print('Expected:')
        print(expected)
        self.assertEqual(dict(ret), dict(expected))

    def test__get_pds_products_multiple_opusid(self):
        "[test_file_utils.py] get_pds_products: versions multiple opusids path"
        opus_id_list = ['co-iss-n1460960868',
                        'co-uvis-euv2001_001_02_12',
                        'co-vims-v1484504505_ir',
                        'vg-iss-2-s-c4360048']
        ret = get_pds_products(opus_id_list, loc_type='path')
        expected = {'co-iss-n1460960868': {'Current': {('Cassini ISS', 0, 'coiss_raw', 'Raw Image'): [settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.IMG', settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.LBL', settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/label/prefix2.fmt', settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/label/tlmtab.fmt'], ('Cassini ISS', 10, 'coiss_calib', 'Calibrated Image'): [settings.PDS_DATA_DIR+'/calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1_CALIB.IMG', settings.PDS_DATA_DIR+'/calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1_CALIB.LBL'], ('Cassini ISS', 110, 'coiss_thumb', 'Extra Preview (thumbnail)'): [settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/extras/thumbnail/1460960653_1461048959/N1460960868_1.IMG.jpeg_small'], ('Cassini ISS', 120, 'coiss_medium', 'Extra Preview (medium)'): [settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/extras/browse/1460960653_1461048959/N1460960868_1.IMG.jpeg'], ('Cassini ISS', 130, 'coiss_full', 'Extra Preview (full)'): [settings.PDS_DATA_DIR+'/volumes/COISS_2xxx/COISS_2002/extras/full/1460960653_1461048959/N1460960868_1.IMG.png'], ('Cassini ISS', 140, 'coiss_documentation', 'Documentation'): [settings.PDS_DATA_DIR+'/documents/COISS_0xxx/VICAR-File-Format.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/ISS-Users-Guide.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/ISS-Users-Guide.docx', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Data-Product-SIS.txt', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Data-Product-SIS.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Cassini-ISS-Final-Report.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Calibration-Theoretical-Basis.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Calibration-Plan.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/CISSCAL-Users-Guide.pdf', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Archive-SIS.txt', settings.PDS_DATA_DIR+'/documents/COISS_0xxx/Archive-SIS.pdf'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): [settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_index.tab', settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_index.lbl'], ('metadata', 10, 'inventory', 'Target Body Inventory'): [settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_inventory.csv', settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_inventory.lbl'], ('metadata', 20, 'planet_geometry', 'Planet Geometry Index'): [settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_saturn_summary.tab', settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_saturn_summary.lbl'], ('metadata', 30, 'moon_geometry', 'Moon Geometry Index'): [settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_moon_summary.tab', settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_moon_summary.lbl'], ('metadata', 40, 'ring_geometry', 'Ring Geometry Index'): [settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_ring_summary.tab', settings.PDS_DATA_DIR+'/metadata/COISS_2xxx/COISS_2002/COISS_2002_ring_summary.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): [settings.PDS_DATA_DIR+'/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1_thumb.jpg'], ('browse', 20, 'browse_small', 'Browse Image (small)'): [settings.PDS_DATA_DIR+'/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1_small.jpg'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): [settings.PDS_DATA_DIR+'/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1_med.jpg'], ('browse', 40, 'browse_full', 'Browse Image (full)'): [settings.PDS_DATA_DIR+'/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1_full.png']}, '2': {('Cassini ISS', 10, 'coiss_calib', 'Calibrated Image'): [settings.PDS_DATA_DIR+'/calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460960868_1_CALIB.IMG', settings.PDS_DATA_DIR+'/calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460960868_1_CALIB.LBL']}, '1': {('Cassini ISS', 10, 'coiss_calib', 'Calibrated Image'): [settings.PDS_DATA_DIR+'/calibrated/COISS_2xxx_v1/COISS_2002/data/1460960653_1461048959/N1460960868_1_CALIB.IMG', settings.PDS_DATA_DIR+'/calibrated/COISS_2xxx_v1/COISS_2002/data/1460960653_1461048959/N1460960868_1_CALIB.LBL']}}, 'co-uvis-euv2001_001_02_12': {'Current': {('Cassini UVIS', 10, 'couvis_raw', 'Raw Data'): [settings.PDS_DATA_DIR+'/volumes/COUVIS_0xxx/COUVIS_0002/DATA/D2001_001/EUV2001_001_02_12.DAT', settings.PDS_DATA_DIR+'/volumes/COUVIS_0xxx/COUVIS_0002/DATA/D2001_001/EUV2001_001_02_12.LBL'], ('Cassini UVIS', 20, 'couvis_calib_corr', 'Calibration Data'): [settings.PDS_DATA_DIR+'/volumes/COUVIS_0xxx/COUVIS_0002/CALIB/VERSION_3/D2001_001/EUV2001_001_02_12_CAL_3.DAT', settings.PDS_DATA_DIR+'/volumes/COUVIS_0xxx/COUVIS_0002/CALIB/VERSION_3/D2001_001/EUV2001_001_02_12_CAL_3.LBL'], ('Cassini UVIS', 30, 'couvis_documentation', 'Documentation'): [settings.PDS_DATA_DIR+'/documents/COUVIS_0xxx/UVIS-Users-Guide.pdf', settings.PDS_DATA_DIR+'/documents/COUVIS_0xxx/UVIS-Users-Guide.docx', settings.PDS_DATA_DIR+'/documents/COUVIS_0xxx/UVIS-Preview-Interpretation-Guide.txt', settings.PDS_DATA_DIR+'/documents/COUVIS_0xxx/UVIS-Archive-SIS.txt', settings.PDS_DATA_DIR+'/documents/COUVIS_0xxx/UVIS-Archive-SIS.pdf', settings.PDS_DATA_DIR+'/documents/COUVIS_0xxx/Cassini-UVIS-Final-Report.pdf'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): [settings.PDS_DATA_DIR+'/metadata/COUVIS_0xxx/COUVIS_0002/COUVIS_0002_index.tab', settings.PDS_DATA_DIR+'/metadata/COUVIS_0xxx/COUVIS_0002/COUVIS_0002_index.lbl'], ('metadata', 9, 'supplemental_index', 'Supplemental Index'): [settings.PDS_DATA_DIR+'/metadata/COUVIS_0xxx/COUVIS_0002/COUVIS_0002_supplemental_index.tab', settings.PDS_DATA_DIR+'/metadata/COUVIS_0xxx/COUVIS_0002/COUVIS_0002_supplemental_index.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): [settings.PDS_DATA_DIR+'/previews/COUVIS_0xxx/COUVIS_0002/DATA/D2001_001/EUV2001_001_02_12_thumb.png'], ('browse', 20, 'browse_small', 'Browse Image (small)'): [settings.PDS_DATA_DIR+'/previews/COUVIS_0xxx/COUVIS_0002/DATA/D2001_001/EUV2001_001_02_12_small.png'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): [settings.PDS_DATA_DIR+'/previews/COUVIS_0xxx/COUVIS_0002/DATA/D2001_001/EUV2001_001_02_12_med.png'], ('browse', 40, 'browse_full', 'Browse Image (full)'): [settings.PDS_DATA_DIR+'/previews/COUVIS_0xxx/COUVIS_0002/DATA/D2001_001/EUV2001_001_02_12_full.png']}}, 'co-vims-v1484504505_ir': {'Current': {('Cassini VIMS', 0, 'covims_raw', 'Raw Cube'): [settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4.qub', settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4.lbl', settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/label/band_bin_center.fmt', settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/label/core_description.fmt', settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/label/suffix_description.fmt'], ('Cassini VIMS', 110, 'covims_thumb', 'Extra Preview (thumbnail)'): [settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/extras/thumbnail/2005015T175855_2005016T184233/v1484504505_4.qub.jpeg_small'], ('Cassini VIMS', 120, 'covims_medium', 'Extra Preview (medium)'): [settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/extras/browse/2005015T175855_2005016T184233/v1484504505_4.qub.jpeg'], ('Cassini VIMS', 130, 'covims_full', 'Extra Preview (full)'): [settings.PDS_DATA_DIR+'/volumes/COVIMS_0xxx/COVIMS_0006/extras/tiff/2005015T175855_2005016T184233/v1484504505_4.qub.tiff'], ('Cassini VIMS', 140, 'covims_documentation', 'Documentation'): [settings.PDS_DATA_DIR+'/documents/COVIMS_0xxx/VIMS-Preview-Interpretation-Guide.pdf', settings.PDS_DATA_DIR+'/documents/COVIMS_0xxx/Data-Product-SIS.txt', settings.PDS_DATA_DIR+'/documents/COVIMS_0xxx/Cassini-VIMS-Final-Report.pdf', settings.PDS_DATA_DIR+'/documents/COVIMS_0xxx/Archive-SIS.txt'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): [settings.PDS_DATA_DIR+'/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_index.tab', settings.PDS_DATA_DIR+'/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_index.lbl'], ('metadata', 9, 'supplemental_index', 'Supplemental Index'): [settings.PDS_DATA_DIR+'/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_supplemental_index.tab', settings.PDS_DATA_DIR+'/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_supplemental_index.lbl'], ('metadata', 10, 'inventory', 'Target Body Inventory'): [settings.PDS_DATA_DIR+'/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.csv', settings.PDS_DATA_DIR+'/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): [settings.PDS_DATA_DIR+'/previews/COVIMS_0xxx/COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4_thumb.png'], ('browse', 20, 'browse_small', 'Browse Image (small)'): [settings.PDS_DATA_DIR+'/previews/COVIMS_0xxx/COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4_small.png'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): [settings.PDS_DATA_DIR+'/previews/COVIMS_0xxx/COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4_med.png'], ('browse', 40, 'browse_full', 'Browse Image (full)'): [settings.PDS_DATA_DIR+'/previews/COVIMS_0xxx/COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4_full.png']}}, 'vg-iss-2-s-c4360048': {'Current': {('Voyager ISS', 0, 'vgiss_raw', 'Raw Image'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_RAW.IMG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_RAW.LBL'], ('Voyager ISS', 10, 'vgiss_cleaned', 'Cleaned Image'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_CLEANED.IMG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_CLEANED.LBL'], ('Voyager ISS', 20, 'vgiss_calib', 'Calibrated Image'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_CALIB.IMG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_CALIB.LBL'], ('Voyager ISS', 30, 'vgiss_geomed', 'Geometrically Corrected Image'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_GEOMED.IMG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_GEOMED.LBL'], ('Voyager ISS', 40, 'vgiss_resloc', 'Reseau Table'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_RESLOC.TAB', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_RESLOC.DAT', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_RESLOC.LBL'], ('Voyager ISS', 50, 'vgiss_geoma', 'Geometric Tiepoint Table'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_GEOMA.TAB', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_GEOMA.DAT', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_GEOMA.LBL'], ('Voyager ISS', 60, 'vgiss_raw_browse', 'Extra Preview (raw)'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_RAW.JPG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_RAW.LBL'], ('Voyager ISS', 70, 'vgiss_cleaned_browse', 'Extra Preview (cleaned)'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_CLEANED.JPG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_CLEANED.LBL'], ('Voyager ISS', 80, 'vgiss_calib_browse', 'Extra Preview (calibrated)'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_CALIB.JPG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_CALIB.LBL'], ('Voyager ISS', 90, 'vgiss_geomed_browse', 'Extra Preview (geometrically corrected)'): [settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_GEOMED.JPG', settings.PDS_DATA_DIR+'/volumes/VGISS_6xxx/VGISS_6210/BROWSE/C43600XX/C4360048_GEOMED.LBL'], ('Voyager ISS', 100, 'vgiss_documentation', 'Documentation'): [settings.PDS_DATA_DIR+'/documents/VGISS_5xxx/VICAR-File-Format.pdf', settings.PDS_DATA_DIR+'/documents/VGISS_5xxx/User-Tutorial.txt', settings.PDS_DATA_DIR+'/documents/VGISS_5xxx/Saturn-Image-Anomalies.txt', settings.PDS_DATA_DIR+'/documents/VGISS_5xxx/Jupiter-Image-Anomalies.txt', settings.PDS_DATA_DIR+'/documents/VGISS_5xxx/Image-Processing.txt', settings.PDS_DATA_DIR+'/documents/VGISS_5xxx/CDROM-Info.txt'], ('metadata', 5, 'rms_index', 'RMS Node Augmented Index'): [settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_index.tab', settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_index.lbl'], ('metadata', 7, 'raw_image_index', 'Raw Image Index'): [settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_raw_image_index.tab', settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_raw_image_index.lbl'], ('metadata', 9, 'supplemental_index', 'Supplemental Index'): [settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_supplemental_index.tab', settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_supplemental_index.lbl'], ('metadata', 10, 'inventory', 'Target Body Inventory'): [settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_inventory.csv', settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_inventory.lbl'], ('metadata', 20, 'planet_geometry', 'Planet Geometry Index'): [settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_saturn_summary.tab', settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_saturn_summary.lbl'], ('metadata', 40, 'ring_geometry', 'Ring Geometry Index'): [settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_ring_summary.tab', settings.PDS_DATA_DIR+'/metadata/VGISS_6xxx/VGISS_6210/VGISS_6210_ring_summary.lbl'], ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)'): [settings.PDS_DATA_DIR+'/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_thumb.jpg'], ('browse', 20, 'browse_small', 'Browse Image (small)'): [settings.PDS_DATA_DIR+'/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_small.jpg'], ('browse', 30, 'browse_medium', 'Browse Image (medium)'): [settings.PDS_DATA_DIR+'/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_med.jpg'], ('browse', 40, 'browse_full', 'Browse Image (full)'): [settings.PDS_DATA_DIR+'/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360048_full.jpg']}}}
        print('Got:')
        print(ret)
        print('Expected:')
        print(expected)
        self.assertEqual(dict(ret), dict(expected))
