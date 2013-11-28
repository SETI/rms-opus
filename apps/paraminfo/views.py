from paraminfo.models import *

def getParamInfoObjectFromSlug(request_get):
    param_info = ParamInfo.objects
    if 'surface_target' in request_get:
        param_info = param_info.filter(category_name__contains=request_get['surface_target'])
    else:
        param_info = param_info.exclude(category_name__contains='obs_surface_geometry')
    return param_info