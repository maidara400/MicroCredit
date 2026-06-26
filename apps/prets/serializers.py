from rest_framework import serializers
from .models import Pret, Echeance
from apps.users.serializers import UserSerializer


class EcheanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Echeance
        fields = ['id', 'numero', 'montant_du', 'date_echeance', 'date_paiement', 'statut']
        read_only_fields = fields


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
