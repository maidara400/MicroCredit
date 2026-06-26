from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer, UserAdminSerializer
from .permissions import IsAdminRole

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Inscription d'un nouveau client",
        description="Crée un compte client. Le rôle est automatiquement défini à 'client'.",
        examples=[
            OpenApiExample('Exemple inscription', value={
                'email': 'client@example.com',
                'username': 'client01',
                'first_name': 'Fatou',
                'last_name': 'Diallo',
                'telephone': '77 000 00 00',
                'password': 'Secret1234!',
                'password2': 'Secret1234!'
            })
        ]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Profil de l'utilisateur connecté")
    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)


class AdminUserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminRole]

    @extend_schema(summary="[Admin] Lister tous les utilisateurs")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="[Admin] Créer un utilisateur (agent ou client)")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminRole]

    @extend_schema(summary="[Admin] Modifier ou désactiver un utilisateur")
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(summary="[Admin] Statistiques globales de la plateforme")
    def get(self, request):
        from apps.demandes.models import DemandePret
        from apps.prets.models import Pret, Echeance
        from django.db.models import Sum, Count, Q, TruncMonth
        from django.utils import timezone
        import datetime

        six_mois = timezone.now() - datetime.timedelta(days=180)
        demandes_par_mois = (
            DemandePret.objects.filter(date_soumission__gte=six_mois)
            .annotate(mois=TruncMonth('date_soumission'))
            .values('mois')
            .annotate(
                total=Count('id'),
                approuvees=Count('id', filter=Q(statut='approuve'))
            )
            .order_by('mois')
        )

        stats = {
            'utilisateurs': {
                'total': User.objects.count(),
                'clients': User.objects.filter(role='client').count(),
                'agents': User.objects.filter(role='agent').count(),
                'admins': User.objects.filter(role='admin').count(),
                'actifs': User.objects.filter(is_active=True).count(),
            },
            'demandes': {
                'total': DemandePret.objects.count(),
                'en_attente': DemandePret.objects.filter(statut='en_attente').count(),
                'approuvees': DemandePret.objects.filter(statut='approuve').count(),
                'refusees': DemandePret.objects.filter(statut='refuse').count(),
            },
            'prets': {
                'total': Pret.objects.count(),
                'actifs': Pret.objects.filter(statut='actif').count(),
                'soldes': Pret.objects.filter(statut='solde').count(),
                'montant_total_prete': Pret.objects.aggregate(total=Sum('montant_total'))['total'] or 0,
            },
            'remboursements': {
                'echeances_payees': Echeance.objects.filter(statut='paye').count(),
                'echeances_en_attente': Echeance.objects.filter(statut='en_attente').count(),
                'echeances_en_retard': Echeance.objects.filter(statut='en_retard').count(),
                'montant_rembourse': Echeance.objects.filter(statut='paye').aggregate(total=Sum('montant_du'))['total'] or 0,
            },
            'activite_mensuelle': [
                {
                    'mois': item['mois'].strftime('%b %Y'),
                    'demandes': item['total'],
                    'approuvees': item['approuvees'],
                }
                for item in demandes_par_mois
            ],
        }
        return Response(stats)
