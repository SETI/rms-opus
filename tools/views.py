from django.shortcuts import get_object_or_404        
import settings


def find_ring_obs_id(request):
    from results.models import Files 
    
    file_spec = request.GET.get('ring_obs_id',False)

    param = 'ring_obs_id'                           
                       
    file_spec = file_spect.split('.')[0];
    
    #if file_spec ends in thumb/small/med/large then break that off too.
    
    # don't you judge me!
    query = "select %s from files where concat(volume_id, '/', file_specification_name) like %s;"; 
    fields = param,file_spec 
    file_spec = file_spec + '%'             
    
    
def error_log(msg):   
    import datetime
    
    path = settings.ERROR_LOG_PATH
    
    
