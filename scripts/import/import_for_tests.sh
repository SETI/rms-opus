#!/bin/bash
#
# Run this from the root of the repository, with rms-opus installed in the active
# environment, with OPUS_CONFIG naming the OPUS configuration file.
set -e

echo "*************************************************************"
echo "***** About to import TEST PDS DATA into a new database *****"
echo "*************************************************************"
echo
echo "About to ERASE and import to this database:"
grep "^schema" "${OPUS_CONFIG:?OPUS_CONFIG must name the OPUS configuration file}"
echo "Note this should be the test-style name"
echo -n ">>> Type YES to continue: "
read yn
if [ "$yn" != "YES" ]; then
    echo "Aborting"
    exit 1
fi
python -m opus_import --scorched-earth --yes $1
# Every bundle is registered first, in the order the imports below take them, which fixes
# each bundle's number and the range its observation ids come from.
/seti/newnav/capped-run.sh python -m opus_import --register-bundles COISS_2002,COISS_2008,COISS_2111 COUVIS_0002 \
    COVIMS_0006 COCIRS_5408 GO_0016,GO_0017,GO_0018 VGISS_6210,VGISS_8201 \
    HSTI1_3667,HSTI1_1559,HSTJ0_9975,HSTJ1_1085,HSTN0_7181,HSTO0_7316,HSTU0_5642 \
    NHPELO_1001,NHLAMV_1001,NHJUMV_1001 EBROCC_0001 CORSS_8001 COUVIS_8001 COVIMS_8001 \
    VG_28xx COCIRS_0406,COCIRS_1003 uranus_occ_u0_kao_91cm \
    cassini_uvis_solarocc_beckerjarmak2023 $1
python -m opus_import --import COISS_2002,COISS_2008,COISS_2111 $1
python -m opus_import --import COUVIS_0002 $1
python -m opus_import --import COVIMS_0006 $1
python -m opus_import --import COCIRS_5408 $1
python -m opus_import --import GO_0016,GO_0017,GO_0018 $1
python -m opus_import --import VGISS_6210,VGISS_8201 $1
python -m opus_import --import HSTI1_3667,HSTI1_1559,HSTJ0_9975,HSTJ1_1085,HSTN0_7181,HSTO0_7316,HSTU0_5642 $1
python -m opus_import --import NHPELO_1001,NHLAMV_1001,NHJUMV_1001 $1
python -m opus_import --import EBROCC_0001 $1
python -m opus_import --import CORSS_8001 $1
python -m opus_import --import COUVIS_8001 $1
python -m opus_import --import COVIMS_8001 $1
python -m opus_import --import VG_28xx $1
python -m opus_import --import COCIRS_0406,COCIRS_1003 $1
python -m opus_import --import uranus_occ_u0_kao_91cm $1
python -m opus_import --import cassini_uvis_solarocc_beckerjarmak2023 $1
# python -m opus_import --import cassini_iss_fring_mosaics_rsfrench2025 $1
python -m opus_import --finalize
python -m opus_import --import-dictionary
python manage.py migrate
python -m opus_import --validate
python -m opus_import --write-schema-version

echo "ALL DONE!"

exit 0
