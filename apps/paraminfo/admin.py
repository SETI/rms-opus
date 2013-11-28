from django.contrib import admin
from paraminfo.models import *
# import settings

from django import forms


from django.core.urlresolvers import reverse




class ParamInfoAdmin(admin.ModelAdmin):
    model = ParamInfo
    list_display = ('name','rank','slug','category','mission','instrument','display','display_results','disp_order')
    list_editable = ('category','rank','display','display_results','disp_order')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    list_filter = ('category',)
    ordering = ('disp_order','id')
admin.site.register(ParamInfo, ParamInfoAdmin)





class CategoryAdmin(admin.ModelAdmin):
    model = ParamInfo
    list_display = ('name','param_info_link','label','group','display','disp_order')
    list_editable = ('label','display','group','disp_order')
    search_fields = ('name', 'label')
    list_filter = ('group',)
    ordering = ('disp_order','id')

    def param_info_link(self, obj):
        url = reverse('admin:paraminfo_paraminfo_changelist')
        return '<a href="%s?category__id__exact=%s">%s Params</a>' % (url, obj.pk, obj.name)
    param_info_link.allow_tags = True



admin.site.register(Category, CategoryAdmin)




class GroupAdmin(admin.ModelAdmin):
    model = ParamInfo
    list_display = ('name','category_link','display','disp_order')
    # list_display_links = ('name',)
    list_editable = ('display','disp_order')
    search_fields = ('name',)
    #list_filter = ('group','category',)
    ordering = ('disp_order','id')

    def category_link(self, obj):
        url = reverse('admin:paraminfo_category_changelist')
        return '<a href="%s?group__id__exact=%s">%s Categories</a>' % (url, obj.pk, obj.name)
    category_link.allow_tags = True


    """
    def changelist_links(self,obj):
        # return 'hilo'
        # return '<img width = "200px" src = "http://farm6.static.flickr.com/5050/5379129975_31bfa67c2a_z.jpg">'
        return '<a href="/admin/paraminfo/paraminfo/?category__id__exact=%s/">cats</a>' % obj.category

    changelist_links.allow_tags = True
    changelist_links.short_description = "cateogireeees"
    """


admin.site.register(Group, GroupAdmin)
