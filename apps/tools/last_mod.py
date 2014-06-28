import datetime
from deploy_datetime import deploy_dt

def last_mod():
    # datetime.datetime.utcnow()
    return datetime.datetime.strptime(deploy_dt)


