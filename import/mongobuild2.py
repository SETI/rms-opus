# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/users/lballard/projects/')
sys.path.append('/users/lballard/projects/opus/')
from opus import settings  
from django.core.management import setup_environ 
setup_environ(settings)

# app imports
from paraminfo.models import *
from search.models import *
from pymongo import Connection 

# connect to mongo
connection = Connection()
db = connection.opus5
mongo_obs = db.obs
 
# create the categor   
print "building category structure and assigning mongodb index keys"     

def getCatLabel(cat_name, cats, trim):         
    label = cat_name.strip().split(' ')[0][0:2] + cat_name.strip().split(' ')[-1][0:trim] 
    if label in cats:
        return getCatLabel(cat.name,cats,trim+1)
    return label    


         
categories = {}                                   
for cat in Category.objects.all():
    cat_label = getCatLabel(cat.name, categories, 1)
    
    mongo_obs.ensure_index([(cat_label+'.n',1), (cat_label+'.v',1)])

    for param in ParamInfo.objects.filter(category=cat.id).order_by("disp_order"):
        try:
            categories[cat_label] += [param.name]
        except KeyError:
            categories[cat_label] = [param.name]
print "done" 

print "getting data"            
# get the data    

count = Observations.objects.all().count()   
# count = 10000
offset = 0   
chunksize = 500

while offset < count:     
    print "starting " + str(offset) + ' to ' + str(offset+ chunksize - 1)
    for obs in Observations.objects.all().values()[offset:offset+chunksize]:  
        observation = {}            
        print "\n\n++++++++++++++++++++++++++++++++++++++++++++++++\n"   
        for cat in categories:
            observation[cat] = []
            for param in categories[cat]:
                if obs[param]: 
                    observation[cat].append({'n':param, 'v':obs[param]})
            if not observation[cat]:
                del observation[cat]
                    
        for cat in observation:
            if observation[cat]:
                print "\n===========\n" + cat + "\n=============\n"
                for paramval in observation[cat]:
                    print str(paramval)
            else:
                del observation[cat]
            
        mongo_obs.insert(observation)   
        print "Inserted"  
    offset = offset + chunksize    
                         

"""        
x = {
    geo: { 'ring_radius1':23423, 'ring_radius2':2340234, 'phase1':23, 'phase2':234 }
}        
"""