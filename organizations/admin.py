from django.contrib import admin
from .models import Organization, OrganizationInvitation

admin.site.register(Organization)
admin.site.register(OrganizationInvitation)
