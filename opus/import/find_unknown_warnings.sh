rm -f __tmp1 __tmp2
grep -v SUMMARY $1 | grep -v -i deleting > __tmp1

S="missing ring geometry files"
echo $S
echo 22 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="missing body surface geometry files"
echo $S
echo 22 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="HSTO0_6854.*Converting bad observation_type IMAGING"
echo $S
echo 1 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="HSTO0_6854.*Converting bad observation_type SPECTROSCOPIC"
echo $S
echo 1 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="HSTO.*MAXIMUM_WAVELENGTH < MINIMUM_WAVELENGTH; swapping"
echo $S
echo 209 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="HSTO.*MAXIMUM_WAVELENGTH_RESOLUTION < MINIMUM_WAVELENGTH_RESOLUTION; swapping"
echo $S
echo 22 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="obs_instrument_gossi/frame_duration"
echo $S
echo 1 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

cp __tmp2 __tmp1

cat __tmp2 | grep -v "$S" > __tmp1
S="No description for item 2071"
echo $S
echo 1 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="COVIMS.*are in the wrong order - setting to time1"
echo $S
echo 251 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="COUVIS.*are in the wrong order - setting to time1"
echo $S
echo 3 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="COCIRS.*are in the wrong order - setting to time1"
echo $S
echo 8 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="Using CLEAR instead of polarized filter for unknown COISS filter combination"
echo $S
echo 20 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="COCIRS.*Badly formatted SPACECRAFT_CLOCK_STOP_COUNT"
echo $S
echo 2 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="COCIRS.*are in the wrong order - setting to count1"
echo $S
echo 6 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

cp __tmp2 __tmp1

S="COISS.*are in the wrong order - setting to count1"
echo $S
echo 280 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2

S="COISS.*are in the wrong order - setting to ert1"
echo $S
echo 81 `cat __tmp2 | grep "$S" | wc -l`
cat __tmp2 | grep -v "$S" > __tmp1

S="Ignoring unknown COISS filter combination"
echo $S
echo 21 `cat __tmp1 | grep "$S" | wc -l`
cat __tmp1 | grep -v "$S" > __tmp2
