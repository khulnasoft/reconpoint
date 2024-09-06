from django.contrib import admin

from .models import *

admin.site.register(Domain)
admin.site.register(Organization)
admin.site.register(RelatedDomain)
admin.site.register(Registrar)
admin.site.register(DomainRegistration)
admin.site.register(DomainInfo)
