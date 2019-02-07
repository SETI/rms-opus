import glob

import log_analyzer

if __name__ == '__main__':
    args = ['--batch', '--html', '--xxlocal', "--dns", "-o", "/users/fy/www/test.html"]
    # args = ['--batch', '--by-time', '--xxlocal', "-o", "/tmp/1"]
    # args = ['--xxfake', '--xxlocal',  '--dns', '-o', '/tmp/realtime']
    # args = ['--slug-summary', '-o', '/tmp/1']

    # args.append('--realtime')

    # args.append("--dns")
    # args.extend(glob.glob("/users/fy/SETI/logs/tools.pds_access_log-201?-??-??"))
    # args.extend(glob.glob("/users/fy/SETI/logs/tools.pds_access_log-*"))
    args.extend(glob.glob("/users/fy/SETI/logs/tools.pds_access_log-2018-12-2[4567]"))

    log_analyzer.main(args)

