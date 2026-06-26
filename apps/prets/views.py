from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db.models import Q

from .models import Pret, Echeance
from .serializers import PretSerializer, EcheanceSerializer
from apps.users.permissions import IsClient, IsAgentOrAdmin


class PretListView(generics.ListAPIView):
    serializer_class = PretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Pret.objects.select_related('client', 'demande')
        if user.is_client:
            qs = qs.filter(client=user)
        statut = self.request.query_params.get('statut')
        search = self.request.query_params.get('search')
        if statut:
            qs = qs.filter(statut=statut)
        if search and not user.is_client:
            qs = qs.filter(
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search) |
                Q(client__email__icontains=search)
            )
        return qs

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


class ClientDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="[Client] Données complètes du tableau de bord")
    def get(self, request):
        from apps.demandes.models import DemandePret
        from django.db.models import Sum

        client = request.user
        demandes = DemandePret.objects.filter(client=client)
        prets = Pret.objects.filter(client=client)
        pret_actif = prets.filter(statut='actif').first()

        data = {
            'demandes': {
                'total': demandes.count(),
                'en_attente': demandes.filter(statut='en_attente').count(),
                'approuvees': demandes.filter(statut='approuve').count(),
                'refusees': demandes.filter(statut='refuse').count(),
            },
            'prets': {
                'total': prets.count(),
                'actifs': prets.filter(statut='actif').count(),
                'soldes': prets.filter(statut='solde').count(),
                'montant_total_emprunte': prets.aggregate(total=Sum('montant_total'))['total'] or 0,
            },
            'pret_actif': None,
        }

        if pret_actif:
            echeances = pret_actif.echeances.all()
            data['pret_actif'] = {
                'id': pret_actif.id,
                'montant_total': float(pret_actif.montant_total),
                'mensualite': float(pret_actif.mensualite),
                'duree_mois': pret_actif.duree_mois,
                'date_debut': pret_actif.date_debut,
                'date_fin_prevue': pret_actif.date_fin_prevue,
                'echeances_payees': pret_actif.echeances_payees,
                'echeances_restantes': pret_actif.echeances_restantes,
                'montant_rembourse': float(pret_actif.montant_rembourse),
                'montant_restant': float(pret_actif.montant_restant),
                'progression_pct': round((pret_actif.echeances_payees / pret_actif.duree_mois) * 100, 1) if pret_actif.duree_mois else 0,
                'prochaine_echeance': None,
            }
            prochaine = echeances.exclude(statut='paye').order_by('numero').first()
            if prochaine:
                data['pret_actif']['prochaine_echeance'] = {
                    'id': prochaine.id,
                    'numero': prochaine.numero,
                    'montant_du': float(prochaine.montant_du),
                    'date_echeance': prochaine.date_echeance,
                    'statut': prochaine.statut,
                }
        return Response(data)


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
