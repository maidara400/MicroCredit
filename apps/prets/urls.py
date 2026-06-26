from django.urls import path
from .views import PretListView, PretDetailView, PretEcheancesView, PayerEcheanceView, EcheancesEnRetardView, ClientDashboardView

urlpatterns = [
    path('dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('', PretListView.as_view(), name='pret-list'),
    path('<int:pk>/', PretDetailView.as_view(), name='pret-detail'),
    path('<int:pk>/echeances/', PretEcheancesView.as_view(), name='pret-echeances'),
    # echeances/en-retard/ doit être AVANT echeances/<int:pk>/ pour éviter le conflit
    path('echeances/en-retard/', EcheancesEnRetardView.as_view(), name='echeances-en-retard'),
    path('echeances/<int:pk>/payer/', PayerEcheanceView.as_view(), name='echeance-payer'),
]
