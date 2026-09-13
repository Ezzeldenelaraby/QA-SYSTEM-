from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    NCRViewSet,
    InspectionListCreateAPIView,
    CalibrationVerifyAPIView,
    DashboardKPIsAPIView,
    api_docs_view,
)

app_name = 'api'

router = DefaultRouter()
router.register(r'ncr', NCRViewSet, basename='ncr')

urlpatterns = [
    # Developer & Shop-Floor Integration Documentation Portal
    path('docs/', api_docs_view, name='docs'),

    # Token Authentication Endpoint for IoT and external systems
    path('token/', obtain_auth_token, name='api-token-auth'),

    # Shop-floor Gauges & CMM Measurements Ingestion
    path('inspections/', InspectionListCreateAPIView.as_view(), name='inspection-list-create'),

    # Instant Gauge Calibration Verification
    path('calibration/verify/<str:identifier>/', CalibrationVerifyAPIView.as_view(), name='calibration-verify'),

    # Real-Time Plant Quality KPIs Feed for TV / SCADA / Andon
    path('dashboard/kpis/', DashboardKPIsAPIView.as_view(), name='dashboard-kpis'),

    # Router endpoints (NCR CRUD)
    path('', include(router.urls)),
]
