from metrics.models import Metrics

def update_metrics(request):
    """ updates the metrics database """
    if not request:
        return  # this is a test running

    session_id = request.session.session_key

    if not session_id:
        # this user has barely touched the homepage #todo test this better
        return


    ip_address = get_client_ip(request)
    m,v = Metrics.objects.using('metrics').get_or_create(session_id=session_id, ip_address=ip_address)
    m.save()

def get_client_ip(request):
    """ gets client ip address from browser """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
