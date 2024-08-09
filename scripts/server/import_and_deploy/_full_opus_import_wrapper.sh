#!/bin/bash
${IMPORT_SCRIPT_DIR}/_run_full_opus_import.sh > ${NOHUP_LOGFILE} 2>&1
if [ $? -eq 0 ]; then
    RESULT="succeeded"
else
    RESULT="FAILED"
fi

mail -s "OPUS import ${RESULT}" rfrench@seti.org < ${NOHUP_LOGFILE}
