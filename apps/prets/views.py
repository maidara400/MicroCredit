from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.utils import timezone

from .models import Pret, Echeance
from .serializers import PretSerializer, EcheanceSerializer
from apps.users.permissions import IsClient, IsAgentOrAdmin


class PretListView(generics.ListAPIView):
    serializer_class = PretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_client:
            return Pret.objects.filter(client=user).select_related('client', 'demande')
        return Pret.objects.all().select_related('client', 'demande')

    @extend_schema(summary="Lister les prêts (les siens pour client, tous pour agent/admin)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PretDetailView(generics.RetrieveAPIView):
    serializer_class = PretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_client:
            return Pret.objects.filter(client=user)
        return Pret.objects.all()

    @extend_schema(summary="Détail d'un prêt avec statistiques de remboursement")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PretEcheancesView(generics.ListAPIView):
    serializer_class = EcheanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        pret_pk = self.kwargs['pk']
        if user.is_client:
            return Echeance.objects.filter(pret__pk=pret_pk, pret__client=user)
        return Echeance.objects.filter(pret__pk=pret_pk)

    @extend_schema(summary="Plan de remboursement d'un prêt (toutes les échéances)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PayerEcheanceView(APIView):
    permission_classes = [IsClient]

    @extend_schema(
        summary="[Client] Enregistrer le paiement d'une échéance",
        description="Marque l'échéance comme payée. Si c'est la dernière, le prêt passe au statut 'soldé'.",
        responses={200: EcheanceSerializer}
    )
    def post(self, request, pk):
        try:
            echeance = Echeance.objects.select_related('pret').get(pk=pk, pret__client=request.user)
        except Echeance.DoesNotExist:
            return Response({'detail': 'Échéance introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if echeance.statut == Echeance.STATUT_PAYE:
            return Response({'detail': 'Cette échéance a déjà été payée.'}, status=status.HTTP_400_BAD_REQUEST)

        if echeance.pret.statut != Pret.STATUT_ACTIF:
            return Response({'detail': 'Ce prêt est déjà soldé.'}, status=status.HTTP_400_BAD_REQUEST)

        echeance.statut = Echeance.STATUT_PAYE
        echeance.date_paiement = timezone.now()
        echeance.save()

        # Vérifier si toutes les échéances sont payées → solder le prêt (R8)
        pret = echeance.pret
        if not pret.echeances.exclude(statut=Echeance.STATUT_PAYE).exists():
            pret.statut = Pret.STATUT_SOLDE
            pret.save()
            return Response({
                'detail': 'Paiement enregistré. Félicitations, votre prêt est entièrement remboursé !',
                'echeance': EcheanceSerializer(echeance).data,
                'pret_solde': True,
            })

        return Response({
            'detail': 'Paiement enregistré avec succès.',
            'echeance': EcheanceSerializer(echeance).data,
            'echeances_restantes': pret.echeances_restantes,
            'pret_solde': False,
        })


class EcheancesEnRetardView(generics.ListAPIView):
    serializer_class = EcheanceSerializer
    permission_classes = [IsAgentOrAdmin]

    def get_queryset(self):
        from datetime import date
        # Mettre à jour les statuts en retard automatiquement
        Echeance.objects.filter(
            statut=Echeance.STATUT_EN_ATTENTE,
            date_echeance__lt=date.today()
        ).update(statut=Echeance.STATUT_EN_RETARD)
        return Echeance.objects.filter(statut=Echeance.STATUT_EN_RETARD).select_related('pret', 'pret__client')

    @extend_schema(summary="[Agent/Admin] Lister toutes les échéances en retard")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
