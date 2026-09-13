from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from apps.ncr.models import NCR
from apps.inspections.models import Inspection
from apps.calibration.models import Equipment
from apps.actions.models import Action
from apps.capa.models import CAPA
from .serializers import (
    NCRSerializer,
    InspectionSerializer,
    EquipmentVerificationSerializer,
)

class NCRViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Nonconformance Reports (NCR).
    Used by line tablets, vision inspection systems, and ERP integrations.
    """
    serializer_class = NCRSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = NCR.objects.select_related('department', 'process', 'reported_by', 'responsible_person').all()
        status_param = self.request.query_params.get('status')
        severity_param = self.request.query_params.get('severity')
        department_param = self.request.query_params.get('department')
        search = self.request.query_params.get('search')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if severity_param:
            queryset = queryset.filter(severity=severity_param)
        if department_param:
            queryset = queryset.filter(department_id=department_param)
        if search:
            queryset = queryset.filter(
                Q(ncr_number__icontains=search) |
                Q(product__icontains=search) |
                Q(batch_lot__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset


class InspectionListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for digital QC inspection tools (CMM, digital vernier calipers, smart scales).
    If out-of-tolerance results (NG) are submitted, an NCR is auto-generated.
    """
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inspection.objects.select_related('process', 'inspector').prefetch_related('items').all()


class CalibrationVerifyAPIView(APIView):
    """
    Fast verification endpoint for shop-floor operators and tool-crib checkout stations.
    Lookup by equipment_id or serial number to verify calibration status before tool checkout.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, identifier):
        equipment = Equipment.objects.filter(
            Q(equipment_id__iexact=identifier) | Q(serial_number__iexact=identifier)
        ).first()

        if not equipment:
            return Response(
                {"error": f"Instrument with identifier '{identifier}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Refresh status based on current date
        equipment.update_status()

        serializer = EquipmentVerificationSerializer(equipment)
        data = serializer.data

        # Add operational advisory
        if not data['is_usable']:
            data['advisory'] = "DO NOT USE - Instrument calibration is EXPIRED or OUT OF SERVICE."
            data['allow_checkout'] = False
        elif data['status'] == Equipment.Status.DUE_SOON:
            data['advisory'] = f"WARNING - Instrument due for recalibration in {data['days_until_due']} days."
            data['allow_checkout'] = True
        else:
            data['advisory'] = "APPROVED - Instrument is calibrated and valid for production."
            data['allow_checkout'] = True

        return Response(data, status=status.HTTP_200_OK)


class DashboardKPIsAPIView(APIView):
    """
    Live aggregated Quality KPIs feed for factory-floor Andon TVs and SCADA dashboards.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()

        open_ncrs = NCR.objects.exclude(status=NCR.Status.CLOSED).count()
        critical_ncrs = NCR.objects.filter(
            status=NCR.Status.OPEN,
            severity=NCR.Severity.CRITICAL
        ).count()

        overdue_actions = Action.objects.filter(
            status__in=[Action.Status.OPEN, Action.Status.IN_PROGRESS],
            due_date__lt=today
        ).count()

        total_equipment = Equipment.objects.count()
        expired_calibrations = Equipment.objects.filter(
            Q(status=Equipment.Status.EXPIRED) | Q(next_calibration_date__lt=today)
        ).count()

        compliance_rate = 100.0
        if total_equipment > 0:
            valid_count = total_equipment - expired_calibrations
            compliance_rate = round((valid_count / total_equipment) * 100, 1)

        open_capas = CAPA.objects.exclude(status=CAPA.Status.CLOSED).count()

        system_health = "HEALTHY"
        if critical_ncrs > 0 or overdue_actions > 2 or compliance_rate < 90.0:
            system_health = "ATTENTION_REQUIRED"

        return Response({
            "timestamp": timezone.now().isoformat(),
            "system_health": system_health,
            "metrics": {
                "open_ncrs": open_ncrs,
                "critical_ncrs": critical_ncrs,
                "overdue_actions": overdue_actions,
                "open_capas": open_capas,
                "total_instruments": total_equipment,
                "expired_instruments": expired_calibrations,
                "calibration_compliance_rate_pct": compliance_rate,
            }
        }, status=status.HTTP_200_OK)


def api_docs_view(request):
    """
    Interactive API Documentation & Developer Portal for plant engineers & IT integration.
    """
    from django.shortcuts import render
    from rest_framework.authtoken.models import Token

    token = None
    if request.user.is_authenticated:
        token, _ = Token.objects.get_or_create(user=request.user)

    return render(request, 'api/docs.html', {
        'token': token.key if token else None,
        'system_url': request.build_absolute_uri('/')[:-1]
    })
