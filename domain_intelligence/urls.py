from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DomainAnalysisViewSet, SalesTrainingViewSet

router = DefaultRouter()
router.register(r'analyses', DomainAnalysisViewSet, basename='domain-analysis')
router.register(r'training', SalesTrainingViewSet, basename='sales-training')

urlpatterns = [
    path('', include(router.urls)),
]
