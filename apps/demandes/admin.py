from django.contrib import admin
from .models import DemandePret


@admin.register(DemandePret)
class DemandePretAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'montant', 'duree_mois', 'statut', 'date_soumission', 'agent']
    list_filter = ['statut', 'date_soumission']
    search_fields = ['client__email', 'client__first_name', 'client__last_name']
    readonly_fields = ['date_soumission', 'date_traitement']
