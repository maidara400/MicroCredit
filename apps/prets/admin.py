from django.contrib import admin
from .models import Pret, Echeance


class EcheanceInline(admin.TabularInline):
    model = Echeance
    extra = 0
    readonly_fields = ['numero', 'montant_du', 'date_echeance', 'date_paiement', 'statut']


@admin.register(Pret)
class PretAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'montant_total', 'mensualite', 'duree_mois', 'statut', 'date_debut']
    list_filter = ['statut', 'date_debut']
    search_fields = ['client__email', 'client__first_name']
    inlines = [EcheanceInline]


@admin.register(Echeance)
class EcheanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'pret', 'numero', 'montant_du', 'date_echeance', 'statut', 'date_paiement']
    list_filter = ['statut', 'date_echeance']
