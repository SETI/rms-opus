# comment out all the other js files        

def get_all_files(template_pth, js_pth):
    
    template = open(template_pth)
    all_lines = template.readlines()
    template.close()
    
    found = False  
    my_files = []
    for no,line in enumerate(all_lines):  
    
        if found:
            if line.strip() == "{# end opus.js #}":
                return my_files
            else: 
                if (line.strip() != '<!--') & (line.strip() != '-->'): 
                    js_base_name = line.strip().split('.')[0].split('/').pop()
                    if js_base_name:
                        my_files += [js_pth + js_base_name +'.js']         

        if line.strip() == "{# opus.js #}":
            found = True