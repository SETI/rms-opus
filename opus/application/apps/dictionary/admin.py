# -*- coding: utf-8 -*-
# from __future__ import unicode_literals
#
# from django.contrib import admin
# from django.contrib.sites.models import Site
# from dictionary.models import Definition
#
# # Register your models here.
# admin.autodiscover()
# admin.site.unregister(Site)
#
# admin.site.site_header = 'Welcome to OPUS Dictionary DB Admin'
# admin.site.site_title = 'OPUS Dictionary DB Admin'
# admin.site.site_url = 'https://tools.pds-rings.seti.org/'
# admin.site.index_title = 'OPUS Dictionary Administration'
# admin.empty_value_display = '**Empty**'
#
#
# class MultiDBModelAdmin(admin.ModelAdmin):
#     # A handy constant for the name of the alternate database.
#     using = 'other'
#
#     def save_model(self, request, obj, form, change):
#         # Tell Django to save objects to the 'other' database.
#         obj.save(using=self.using)
#
#     def delete_model(self, request, obj):
#         # Tell Django to delete objects from the 'other' database
#         obj.delete(using=self.using)
#
#     def get_queryset(self, request):
#         # Tell Django to look for objects on the 'other' database.
#         return super(MultiDBModelAdmin, self).get_queryset(request).using(self.using)
#
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         # Tell Django to populate ForeignKey widgets using a query
#         # on the 'other' database.
#         return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)
#
#     def formfield_for_manytomany(self, db_field, request, **kwargs):
#         # Tell Django to populate ManyToMany widgets using a query
#         # on the 'other' database.
#         return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request, using=self.using, **kwargs)
#
# class DefinitionsAdmin(MultiDBModelAdmin):
#     using = 'dictionary'
#     list_display = ('term', 'context', 'definition', 'expanded', 'image_url', 'more_info_label', 'more_info_url')
#     fields = ('term', 'context', 'definition', 'expanded', 'image_url', ('more_info_label', 'more_info_url'))
#     #def get_queryset(self, request):
#         # Tell Django to look for objects on the 'other' database.
#         #return super(MultiDBModelAdmin, self).get_queryset(request).using(self.using)
#
# admin.site.register(Definition, DefinitionsAdmin)
