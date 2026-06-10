from django.apps import AppConfig
from django.contrib import admin

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Customize admin site headers
        admin.site.site_header = "ATO Admin Panel"
        admin.site.site_title = "ATO Admin Panel"
        admin.site.index_title = "Welcome to ATO CRM Administration"
