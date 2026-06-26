from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db import models
from django.db.models import Q

from .models import DemandePret
from .serializers import DemandePretSerializer, DemandePretCreateSerializer, RefuserDemandeSerializer
from apps.users.permissions import IsClient, IsAgentOrAdmin


class DemandePretListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DemandePretCreateSerializer
        return DemandePretSerializer

    def get_queryset(self):
        user = self.request.user
        qs = DemandePret.objects.select_related('client', 'agent')
        if user.is_client:
            qs = qs.filter(client=user)

        # Filtres query params
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

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsClient()]
        return [IsAuthenticated()]

    @extend_schema(summary="[Client] Soumettre une demande de prêt / [Agent/Admin] Lister toutes les demandes")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="[Client] Soumettre une nouvelle demande de prêt")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DemandePretDetailView(generics.RetrieveAPIView):
    serializer_class = DemandePretSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_client:
            return DemandePret.objects.filter(client=user)
        return DemandePret.objects.all()

    @extend_schema(summary="Détail d'une demande de prêt")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ApprouverDemandeView(APIView):
    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="[Agent] Approuver une demande de prêt",
        description="Approuve le dossier et génère automatiquement le prêt avec son plan de remboursement.",
        responses={200: DemandePretSerializer}
    )
    def post(self, request, pk):
        try:
            demande = DemandePret.objects.get(pk=pk)
        except DemandePret.DoesNotExist:
            return Response({'detail': 'Demande introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if demande.statut != DemandePret.STATUT_EN_ATTENTE:
            return Response({'detail': 'Cette demande a déjà été traitée.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mise à jour de la demande
        demande.statut = DemandePret.STATUT_APPROUVE
        demande.agent = request.user
        demande.date_traitement = timezone.now()
        demande.save()

        # Création du prêt et des échéances
        from apps.prets.models import Pret, Echeance, ParametresPret, TranchePret
        from decimal import Decimal, ROUND_HALF_UP
        from datetime import date
        from dateutil.relativedelta import relativedelta

        montant = Decimal(str(demande.montant))
        n = demande.duree_mois
        date_debut = date.today()
        date_fin = date_debut + relativedelta(months=n)

        # Trouver le taux selon la tranche
        tranche = TranchePret.objects.filter(montant_min__lte=montant).filter(
            models.Q(montant_max__isnull=True) | models.Q(montant_max__gte=montant)
        ).order_by('-montant_min').first()

        if tranche:
            taux_annuel = Decimal(str(tranche.taux_annuel))
        else:
            params = ParametresPret.get()
            taux_annuel = Decimal(str(params.taux_defaut))

        # Calcul des mensualités avec intérêts (méthode amortissement constant)
        # taux mensuel = taux_annuel / 12 / 100
        taux_mensuel = taux_annuel / Decimal('12') / Decimal('100')

        echeances_data = []
        if taux_mensuel == 0:
            capital_par_mois = (montant / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            mensualite = capital_par_mois
            montant_interets = Decimal('0')
            capital_restant = montant
            for i in range(1, n + 1):
                cap = capital_par_mois if i < n else capital_restant
                echeances_data.append({'capital': cap, 'interet': Decimal('0'), 'total': cap})
                capital_restant -= cap
        else:
            # Formule annuité constante : M = P * r*(1+r)^n / ((1+r)^n - 1)
            r = taux_mensuel
            facteur = (1 + r) ** n
            mensualite = (montant * r * facteur / (facteur - 1)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            capital_restant = montant
            montant_interets = Decimal('0')
            for i in range(1, n + 1):
                interet = (capital_restant * r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                capital = (mensualite - interet).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                if i == n:
                    # Ajuster la dernière échéance pour solder exactement
                    capital = capital_restant
                    mensualite_i = capital + interet
                else:
                    mensualite_i = mensualite
                montant_interets += interet
                echeances_data.append({'capital': capital, 'interet': interet, 'total': mensualite_i})
                capital_restant -= capital

        pret = Pret.objects.create(
            demande=demande,
            client=demande.client,
            montant_total=montant,
            mensualite=mensualite,
            duree_mois=n,
            taux_annuel=taux_annuel,
            montant_interets=montant_interets,
            date_debut=date_debut,
            date_fin_prevue=date_fin,
        )

        # Générer les N échéances
        echeances_objs = []
        for i, ed in enumerate(echeances_data, 1):
            echeances_objs.append(Echeance(
                pret=pret,
                numero=i,
                montant_capital=ed['capital'],
                montant_interet=ed['interet'],
                montant_du=ed['total'],
                date_echeance=date_debut + relativedelta(months=i),
            ))
        Echeance.objects.bulk_create(echeances_objs)

        return Response({
            'detail': 'Demande approuvée. Prêt créé avec succès.',
            'demande': DemandePretSerializer(demande, context={'request': request}).data,
            'pret_id': pret.pk,
        }, status=status.HTTP_200_OK)


class RefuserDemandeView(APIView):
    permission_classes = [IsAgentOrAdmin]

    @extend_schema(
        summary="[Agent] Refuser une demande de prêt",
        request=RefuserDemandeSerializer,
        responses={200: DemandePretSerializer}
    )
    def post(self, request, pk):
        try:
            demande = DemandePret.objects.get(pk=pk)
        except DemandePret.DoesNotExist:
            return Response({'detail': 'Demande introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if demande.statut != DemandePret.STATUT_EN_ATTENTE:
            return Response({'detail': 'Cette demande a déjà été traitée.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RefuserDemandeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        demande.statut = DemandePret.STATUT_REFUSE
        demande.agent = request.user
        demande.date_traitement = timezone.now()
        demande.motif_refus = serializer.validated_data['motif_refus']
        demande.save()

        return Response({
            'detail': 'Demande refusée.',
            'demande': DemandePretSerializer(demande, context={'request': request}).data,
        }, status=status.HTTP_200_OK)
