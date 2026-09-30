#!/bin/bash
${IMPORT_SCRIPT_DIR}/_run_full_opus_import.sh "$@" > ${NOHUP_LOGFILE} 2>&1
if [ $? -eq 0 ]; then
    RESULT="succeeded"
else
    RESULT="FAILED"
fi

# Who hears about it comes from deploy.env, which run_full_opus_import.sh read before
# it detached this. With nobody named, the log stays where it was written and that is
# the whole report.
if [[ -n ${OPUS_IMPORT_MAIL_TO:-} ]]; then
    mail -s "OPUS import ${RESULT}" "${OPUS_IMPORT_MAIL_TO}" < "${NOHUP_LOGFILE}"
fi
