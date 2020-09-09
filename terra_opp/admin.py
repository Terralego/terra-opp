from django.contrib import admin

from . import models


admin.site.register(models.Viewpoint)
admin.site.register(models.Campaign)
admin.site.register(models.Picture)
admin.site.register(models.City)
admin.site.register(models.Theme)
