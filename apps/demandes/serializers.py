from rest_framework import serializers
from .models import DemandePret
from apps.users.serializers import UserSerializer


class DemandePretSerializer(serializers.ModelSerializer):
    client_detail = UserSerializer(source='client', read_only=True)
    agent_detail = UserSerializer(source='agent', read_only=True)
    mensualite_estimee = serializers.SerializerMethodField()

    class Meta:
        model = DemandePret
        fields = [
            'id', 'client', 'client_detail', 'montant', 'duree_mois',
            'motif', 'statut', 'date_soumission', 'date_traitement',
            'agent', 'agent_detail', 'motif_refus', 'mensualite_estimee'
        ]
        read_only_fields = ['id', 'statut', 'date_soumission', 'date_traitement', 'agent', 'motif_refus']

    def get_mensualite_estimee(self, obj):
        return round(float(obj.montant) / obj.duree_mois, 2)

    def validate(self, attrs):
        request = self.context['request']
        client = request.user
        # R1 : pas de prêt actif
        from apps.prets.models import Pret
        if Pret.objects.filter(client=client, statut='actif').exists():
            raise serializers.ValidationError("Vous avez déjà un prêt actif. Soldez-le avant de faire une nouvelle demande.")
        # R2 : pas de demande en attente
        if DemandePret.objects.filter(client=client, statut='en_attente').exists():
            raise serializers.ValidationError("Vous avez déjà une demande en attente de traitement.")
        return attrs


class DemandePretCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandePret
        fields = ['montant', 'duree_mois', 'motif']

    def validate(self, attrs):
        request = self.context['request']
        client = request.user
        from apps.prets.models import Pret
        if Pret.objects.filter(client=client, statut='actif').exists():
            raise serializers.ValidationError("Vous avez déjà un prêt actif.")
        if DemandePret.objects.filter(client=client, statut='en_attente').exists():
            raise serializers.ValidationError("Vous avez déjà une demande en attente.")
        return attrs

    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)


class RefuserDemandeSerializer(serializers.Serializer):
    motif_refus = serializers.CharField(required=True, min_length=10)
