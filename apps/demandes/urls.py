from django.urls import path
from .views import DemandePretListCreateView, DemandePretDetailView, ApprouverDemandeView, RefuserDemandeView

urlpatterns = [
    path('', DemandePretListCreateView.as_view(), name='demande-list-create'),
    path('<int:pk>/', DemandePretDetailView.as_view(), name='demande-detail'),
    path('<int:pk>/approuver/', ApprouverDemandeView.as_view(), name='demande-approuver'),
    path('<int:pk>/refuser/', RefuserDemandeView.as_view(), name='demande-refuser'),
]
