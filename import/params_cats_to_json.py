import pprint

params_cats_file = '/users/lballard/projects/opus/import/params_cats.json'  
params_cats = open(params_cats_file).readlines()

data = {}   
fields = ['param','rank','value_type','form_type','mandatory_null','units','quick','note']
for line in params_cats:
    if line.find('group:',0) > -1:          # this is a group
        group = line.split(':')[1].strip()
        data[group] = {}
    elif line.find('cat:',0) > -1:       # this is category
        cat = line.split(':')[1].strip()   
        data[group][cat] = {}   
        field_no = 0
    else:                                   # this is a field 
        print "hell " + str(field_no) + ' ' + line.strip()
        field = fields[field_no]  
        data[group][cat][field] = line.strip()         
        field_no += 1

        
pprint.pprint(data)        




