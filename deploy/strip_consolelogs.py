"""
   removes all lines with console.log from all the opus custom javascript files

"""
from  shutil import copyfile
import sys
import string   
from js_files import get_all_files

def stripConsoleLogs(my_files):
    for myfile in my_files:
        backup_file = "/users/lballard/backups/" + myfile.split('/').pop() +'.bak'
        copyfile(myfile, backup_file);

        newlines = []
        f = open(myfile) 
        for line in f.readlines():
            if not line.strip().startswith('console.log'):
                newlines += [line]
        
        new_file = open(myfile,"w")              
        new_file.write(''.join(newlines))
        new_file.close()        

        print ""
        print "ok."
        print "removed console.log statements from " + myfile
        print 'your original file is backed up at ' + backup_file
        print ""
                                             
#------------------------------------------------------------------------------------------#
                                                                 
template_pth = '/users/lballard/projects/opus/ui/templates/base_opus.html'  
outfile = '/users/lballard/projects/opus/static_media/js/opus_all.min.js'

js_pth = '/users/lballard/projects/opus/static_media/js/'
my_files = get_all_files(template_pth, js_pth)
get_all_files(template_pth, js_pth) 
stripConsoleLogs(my_files)

            