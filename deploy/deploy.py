"""
/*********************************************************************************************
 *
 *  Rollout!
 *
 *      this script minifies and concats all custom opus js files
 *      removing any console logs
 *      and edits the base.html template to include the concatenated js file instead of all the others
 *      and makes backups as it goes..
 *
 *
 *********************************************************************************************/
"""
from slimmer import js_slimmer
from strip_consolelogs import stripConsoleLogs
from js_files import get_all_files

# file paths
template_pth = 'opus/ui/templates/base_opus.html'
template_backup_pth = '/users/lballard/backups/base_opus.html'
outfile = 'opus/static_media/js/opus_all.min.js'
js_pth = 'opus/static_media/js/'

# get all js files
my_files = get_all_files(template_pth, js_pth)

# read in and backup template file
template = open(template_pth)
all_lines = template.readlines()
template.close()
backup = open(template_backup_pth,"w")
backup.write("\n".join(all_lines))
backup.close()
print " template backed up at " + template_backup_pth

# uncomment the concatenated js script line in the template
found = False
for no,line in enumerate(all_lines):

    if line.strip() == "{# opus.all.min.js #}":
        found = True

    if found:
        if line.strip() == '<!--':
            del all_lines[no]
        if line.strip() == '-->':
            del all_lines[no]
            break

# comment out all the other js files in the template
found = False
for no,line in enumerate(all_lines):

    if found:
        if line.strip() == "{# end opus.js #}":
            all_lines[no] = "--> \n" + all_lines[no]
            break

    if line.strip() == "{# opus.js #}":
        all_lines[no] = all_lines[no] + "<!--\n"
        found = True

# strip any console log calls from all js files
stripConsoleLogs(my_files)

# min and concat all js files in js_files.py/base_opus.html
min_file = ""
for infile in my_files:
    min_file = min_file + js_slimmer(open(infile).read())

# write out the new template and the js file
new_file = open(template_pth,"w")
new_file.write("".join(all_lines))
new_file.close()
new_file = open(outfile,"w")
new_file.write(min_file)
new_file.close()
print "Bye!"



