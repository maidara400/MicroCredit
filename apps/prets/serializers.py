from rest_framework import serializers
from .models import Pret, Echeance, ParametresPret, TranchePret
from apps.users.serializers import UserSerializer


class TranchePretSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranchePret
        fields = ['id', 'montant_min', 'montant_max', 'taux_annuel', 'libelle']


class ParametresPretSerializer(serializers.ModelSerializer):
    tranches = TranchePretSerializer(source='tranchepret_set', many=True, read_only=True)
    modifie_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = ParametresPret
        fields = ['id', 'montant_min', 'montant_max', 'duree_min', 'duree_max',
                  'taux_defaut', 'date_modification', 'modifie_par_nom', 'tranches']
        read_only_fields = ['id', 'date_modification', 'modifie_par_nom', 'tranches']

    def get_modifie_par_nom(self, obj):
        if obj.modifie_par:
            return f"{obj.modifie_par.first_name} {obj.modifie_par.last_name}"
        return None


class EcheanceSerializer(serializers.ModelSerializer):
    client_nom = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()
    jours_retard = serializers.SerializerMethodField()

    class Meta:
        model = Echeance
        fields = ['id', 'pret', 'numero', 'montant_capital', 'montant_interet', 'montant_du',
                  'date_echeance', 'date_paiement', 'statut', 'client_nom', 'client_email', 'jours_retard']
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
            'montant_total', 'mensualite', 'duree_mois',
            'taux_annuel', 'montant_interets', 'statut',
            'date_debut', 'date_fin_prevue',
            'echeances_payees', 'echeances_restantes',
            'montant_rembourse', 'montant_restant',
        ]
        read_only_fields = fields
