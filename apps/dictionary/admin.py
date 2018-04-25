# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import MultiDBModelAdmin
from .models import Definition
from .models import Definitionsnew

class DefinitionsAdmin(admin.ModelAdmin):
    using = 'dictionary'
    list_display = ('term', 'context', 'definition', 'expanded', 'image_url', 'more_info_url')
    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super(MultiDBModelAdmin, self).get_queryset(request).using(self.using)

admin.site.register(Definitionsnew, DefinitionsAdmin)
