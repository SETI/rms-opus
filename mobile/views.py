from results.models import *
from results.views import *
from search.models import *   
from django.shortcuts import render_to_response
from django.http import HttpResponse
import settings
from django.template import RequestContext  
from django.utils import simplejson
 
def randomImg():
    import random
    imgs = ['PIA11695_modest','PIA08329_modest','PIA08350_modest','PIA12755_modest','PIA12747_modest']    
    return imgs[random.randrange(1,len(imgs))] + '.jpg'
    
def menus(request):
    instruments = Image.objects.all().distinct().values('instrument_id');
    volumes = Image.objects.all().distinct().values('instrument_id','volume_id').order_by('-volume_id');
    homepage_pic = randomImg();
    return render_to_response("menus.html",locals(),context_instance=RequestContext(request))      

def gallery(request,volume_id,page):
    limit=50      
    page = int(page)
    offset = (page-1)*limit +1    
    images = Image.objects.filter(volume_id=volume_id)[offset:offset+limit-1]
    data = {}
    data['data'] = [[i.ring_obs_id, i.thumb] for i in images] 
    data['static'] = settings.IMAGE_HTTP_PATH;
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')
    # return render_to_response("mgallery.html",locals(),context_instance=RequestContext(request))    
  
def image(request,ring_obs_id):         
    img = Image.objects.get(ring_obs_id=ring_obs_id) 
    return render_to_response("mimage.html",locals(),context_instance=RequestContext(request))    
    
def detail(request,ring_obs_id):    
    detail = Observations.objects.get(ring_obs_id=ring_obs_id)    
    fields = ParamInfo.objects.filter(display_results='Y').values('slug')
    return render_to_response("mdetail.html",locals(),context_instance=RequestContext(request))    