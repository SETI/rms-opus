from django.contrib import admin 

from guide.models import *


class KeyValueAdmin(admin.ModelAdmin):    
    model = KeyValue
    list_display = ('id','key','value','disp_order')   
    list_editable = ('key','value','disp_order')       
    list_filter = ('resource',)     
    search_fields = ('key','value')
    ordering = ('disp_order','id')    

admin.site.register(KeyValue, KeyValueAdmin)             
                     
class KeyValueInline(admin.TabularInline):
    model = KeyValue                                            
           

class ExampleAdmin(admin.ModelAdmin):    
    model = Example
    list_display = ('id','intro','link','disp_order')   
    list_editable = ('intro','link','disp_order')       
    search_fields = ('intro','link')
    list_filter = ('resource',)     
    ordering = ('disp_order','id')    

admin.site.register(Example, ExampleAdmin)             

class ExampleInline(admin.TabularInline):
    model = Example                                            

class ResourceAdmin(admin.ModelAdmin):    
    model = Resource       
    inlines = (KeyValueInline,ExampleInline)
    list_display = ('name','desc','disp_order')   
    list_editable = ('desc','disp_order')       
    list_display_links = ('name',) 
    search_fields = ('name', 'desc')
    list_filter = ('group',)     
    ordering = ('disp_order','id')

admin.site.register(Resource, ResourceAdmin)

class GroupAdmin(admin.ModelAdmin):    
    model = Group
    list_display = ('name','desc','disp_order')   
    list_editable = ('desc','disp_order')       
    search_fields = ('name','Desc')
    ordering = ('disp_order','id')    

admin.site.register(Group, GroupAdmin)             
               

    
 
 
