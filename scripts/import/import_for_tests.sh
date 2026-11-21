#!/bin/bash
#
# Run this from the root of the repository, with rms-opus installed in the active
# environment, with OPUS_CONFIG naming the OPUS configuration file. Its arguments are
# options of opus_import_all, such as --workers 24 --importers 6, passed on as given.
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
# The bundles the integration suite's API goldens are pinned to, in the order they are
# registered, which fixes every observation id. A mission's bundles share a line.
TEST_BUNDLES=(
    COISS_2002 COISS_2008 COISS_2111
    COUVIS_0002
    COVIMS_0006
    COCIRS_5408
    GO_0016 GO_0017 GO_0018
    VGISS_6210 VGISS_8201
    HSTI1_3667 HSTI1_1559 HSTJ0_9975 HSTJ1_1085 HSTN0_7181 HSTO0_7316 HSTU0_5642
    NHPELO_1001 NHLAMV_1001 NHJUMV_1001
    EBROCC_0001
    CORSS_8001
    COUVIS_8001
    COVIMS_8001
    VG_28xx
    COCIRS_0406 COCIRS_1003
    uranus_occ_u0_kao_91cm
    cassini_uvis_solarocc_beckerjarmak2023
    # cassini_iss_fring_mosaics_rsfrench2025
)
# Erase the schema, register the list, import it with queue importers (--importers, or
# [import] importers) sharing the workers (--workers, or [import] workers), and finish
# the database. The confirmation above answers the erase's.
opus_import_all --scorched-earth --yes --sets "$(IFS=,; echo "${TEST_BUNDLES[*]}")" "$@"
python manage.py migrate

echo "ALL DONE!"

exit 0
