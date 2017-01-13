from metrics.models import Metrics

def update_metrics(request):
    if not request:
        return  # this is a test running

    if not request.session.get('has_session'):
        # this user has barely touched the homepage #todo test this better
        return

    session_id = request.session.session_key

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
