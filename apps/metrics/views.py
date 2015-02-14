from metrics.models import Metrics

def update_metrics(request):
    try:
        session_id = request.session.session_key
    except AttributeError:
        # no session attribute, this is probably a test running
        return

    ip_address = get_client_ip(request)
    m,v = Metrics.objects.using('metrics').get_or_create(session_id=session_id, ip_address=ip_address)
    m.save()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip