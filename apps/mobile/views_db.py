from results.models import *
from results.views import *
from search.models import *   
from django.shortcuts import render_to_response
from django.http import HttpResponse
import settings
from django.template import RequestContext
  
def menus(request):
    instruments = Image.objects.all().distinct().values('instrument_id');
    volumes = Image.objects.all().distinct().values('instrument_id','volume_id').order_by('-volume_id');
    return render_to_response("menus.html",locals(),context_instance=RequestContext(request))      
                                                         
def gallery(request,volume_id):    
    images = Image.objects.filter(volume_id=volume_id)[0:100] 
    return render_to_response("mgallery.html",locals(),context_instance=RequestContext(request))    
  
def image(request,ring_obs_id):         
    img = Image.objects.get(ring_obs_id=ring_obs_id) 
    return render_to_response("mimage.html",locals(),context_instance=RequestContext(request))    
    
def detail(request,ring_obs_id):    
    detail = Observations.objects.get(ring_obs_id=ring_obs_id)    
    fields = ParamInfo.objects.filter(display_results='Y').values('slug')
    return render_to_response("mdetail.html",locals(),context_instance=RequestContext(request))