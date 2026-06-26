from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    # API
    path('api/auth/', include('apps.users.urls')),
    path('api/demandes/', include('apps.demandes.urls')),
    path('api/prets/', include('apps.prets.urls')),
    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Frontend (SPA)
    path('', TemplateView.as_view(template_name='index.html'), name='frontend'),
]
