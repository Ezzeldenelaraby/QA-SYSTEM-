from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.processes.models import Process
from apps.ncr.models import NCR
from apps.inspections.models import Inspection, InspectionItem
from apps.calibration.models import Equipment
from apps.core.utils import log_audit
from apps.notifications.models import Notification
from apps.core.notifications import send_qms_email

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'role', 'email']


class DepartmentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'code', 'name']


class NCRSerializer(serializers.ModelSerializer):
    reported_by = UserMiniSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    process_name = serializers.CharField(source='process.name', read_only=True)
    responsible_person = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    requirement = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Standard engineering drawing & tolerance specifications"
    )

    class Meta:
        model = NCR
        fields = [
            'id', 'ncr_number', 'date', 'department', 'department_name',
            'process', 'process_name', 'product', 'batch_lot',
            'reported_by', 'source', 'description', 'requirement',
            'evidence', 'classification', 'severity',
            'immediate_correction', 'containment_action', 'root_cause_summary',
            'responsible_person', 'due_date', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'ncr_number', 'reported_by', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else User.objects.filter(is_superuser=True).first()
        validated_data['reported_by'] = user

        # If responsible_person is not provided, default to department manager or user
        if not validated_data.get('responsible_person'):
            dept = validated_data.get('department')
            if dept and dept.manager:
                validated_data['responsible_person'] = dept.manager
            else:
                validated_data['responsible_person'] = user

        ncr = NCR.objects.create(**validated_data)
        log_audit(user, 'CREATE', 'NCR', ncr.id, ncr.ncr_number, notes="Created via REST API")

        if ncr.responsible_person:
            Notification.create_notification(
                recipient=ncr.responsible_person,
                title=f"NCR Assigned via API: {ncr.ncr_number}",
                message=f"New NCR on {ncr.product} logged by external integration.",
                link=f"/ncr/{ncr.id}/"
            )

        if ncr.severity == NCR.Severity.CRITICAL or ncr.classification == NCR.Classification.CRITICAL:
            qa_leaders = User.objects.filter(role__in=[User.Role.QA_MANAGER, User.Role.SUPER_ADMIN], is_active=True)
            for leader in qa_leaders:
                Notification.create_notification(
                    recipient=leader,
                    title=f"🚨 CRITICAL NCR (API): {ncr.ncr_number}",
                    message=f"CRITICAL defect on {ncr.product} ({ncr.department.name}). Immediate containment required!",
                    link=f"/ncr/{ncr.id}/"
                )
            recipient_emails = [l.email for l in qa_leaders if l.email]
            if recipient_emails:
                send_qms_email(
                    subject=f"CRITICAL DEFECT ALERT (API): {ncr.ncr_number} - {ncr.product}",
                    template_name="emails/ncr_critical_alert.html",
                    context={'ncr': ncr},
                    recipient_list=recipient_emails
                )
        return ncr


class InspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields = ['id', 'checkpoint_name', 'specification', 'measured_value', 'unit', 'result', 'comment']


class InspectionSerializer(serializers.ModelSerializer):
    items = InspectionItemSerializer(many=True, required=False)
    inspector = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    inspector_name = serializers.CharField(source='inspector.get_full_name', read_only=True)
    process_name = serializers.CharField(source='process.name', read_only=True)

    class Meta:
        model = Inspection
        fields = [
            'id', 'inspection_number', 'date', 'process', 'process_name',
            'product', 'batch_lot', 'machine', 'inspector', 'inspector_name',
            'shift', 'overall_result', 'comments', 'linked_ncr', 'items'
        ]
        read_only_fields = ['id', 'inspection_number', 'linked_ncr']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        if not validated_data.get('inspector'):
            validated_data['inspector'] = request.user if request and request.user.is_authenticated else User.objects.first()

        inspection = Inspection.objects.create(**validated_data)
        has_defect = False

        for item_data in items_data:
            item = InspectionItem.objects.create(inspection=inspection, **item_data)
            if item.result == InspectionItem.ItemResult.NG:
                has_defect = True

        if has_defect or inspection.overall_result == Inspection.Result.NG:
            resp_person = inspection.process.department.manager or inspection.inspector
            auto_ncr = NCR.objects.create(
                department=inspection.process.department,
                process=inspection.process,
                product=inspection.product,
                batch_lot=inspection.batch_lot,
                reported_by=inspection.inspector,
                responsible_person=resp_person,
                source=NCR.Source.INSPECTION,
                classification=NCR.Classification.MAJOR,
                severity=NCR.Severity.HIGH,
                status=NCR.Status.OPEN,
                due_date=inspection.date,
                description=f"Auto-generated NCR from failed inspection {inspection.inspection_number} on machine {inspection.machine}.",
                requirement="Dimensional / visual inspection tolerance conformance",
                containment_action="Hold batch at inspection gate; segregation in progress."
            )
            inspection.linked_ncr = auto_ncr
            inspection.overall_result = Inspection.Result.NG
            inspection.save(update_fields=['linked_ncr', 'overall_result'])
            log_audit(inspection.inspector, 'CREATE', 'NCR', auto_ncr.id, auto_ncr.ncr_number, notes=f"Auto-triggered by {inspection.inspection_number}")

        return inspection


class EquipmentVerificationSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    is_usable = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Equipment
        fields = [
            'id', 'equipment_id', 'equipment_name', 'category',
            'serial_number', 'department_name', 'location',
            'measurement_range', 'accuracy', 'status', 'status_display',
            'last_calibration_date', 'next_calibration_date',
            'days_until_due', 'is_usable'
        ]

    def get_is_usable(self, obj) -> bool:
        return obj.status in [Equipment.Status.VALID, Equipment.Status.DUE_SOON]
