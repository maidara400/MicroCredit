from rest_framework import serializers
from .models import Pret, Echeance
from apps.users.serializers import UserSerializer


class EcheanceSerializer(serializers.ModelSerializer):
    client_nom = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()
    jours_retard = serializers.SerializerMethodField()

    class Meta:
        model = Echeance
        fields = ['id', 'pret', 'numero', 'montant_du', 'date_echeance', 'date_paiement', 'statut', 'client_nom', 'client_email', 'jours_retard']
        read_only_fields = fields

    def get_client_nom(self, obj):
        return f"{obj.pret.client.first_name} {obj.pret.client.last_name}"

    def get_client_email(self, obj):
        return obj.pret.client.email

    def get_jours_retard(self, obj):
        if obj.statut == 'en_retard':
            from datetime import date
            delta = date.today() - obj.date_echeance
            return delta.days
        return None


class PretSerializer(serializers.ModelSerializer):
    client_detail = UserSerializer(source='client', read_only=True)
    echeances_payees = serializers.IntegerField(read_only=True)
    echeances_restantes = serializers.IntegerField(read_only=True)
    montant_rembourse = serializers.FloatField(read_only=True)
    montant_restant = serializers.FloatField(read_only=True)

    class Meta:
        model = Pret
        fields = [
            'id', 'demande', 'client', 'client_detail',
            'montant_total', 'mensualite', 'duree_mois', 'statut',
            'date_debut', 'date_fin_prevue',
            'echeances_payees', 'echeances_restantes',
            'montant_rembourse', 'montant_restant',
        ]
        read_only_fields = fields
