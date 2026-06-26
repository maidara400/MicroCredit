from django.urls import path
from .views import (
    PretListView, PretDetailView, PretEcheancesView, PayerEcheanceView,
    EcheancesEnRetardView, ClientDashboardView,
    ParametresPretView, TranchePretListCreateView, TranchePretDetailView,
)

urlpatterns = [
    path('dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('', PretListView.as_view(), name='pret-list'),
    path('<int:pk>/', PretDetailView.as_view(), name='pret-detail'),
    path('<int:pk>/echeances/', PretEcheancesView.as_view(), name='pret-echeances'),
    path('echeances/en-retard/', EcheancesEnRetardView.as_view(), name='echeances-en-retard'),
    path('echeances/<int:pk>/payer/', PayerEcheanceView.as_view(), name='echeance-payer'),
    # Config admin
    path('config/parametres/', ParametresPretView.as_view(), name='pret-parametres'),
    path('config/tranches/', TranchePretListCreateView.as_view(), name='tranche-list-create'),
    path('config/tranches/<int:pk>/', TranchePretDetailView.as_view(), name='tranche-detail'),
]
