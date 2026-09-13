from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.actions.models import Action
from apps.calibration.models import Equipment
from apps.training.models import TrainingRecord
from apps.audits.models import AuditPlan
from apps.ncr.models import NCR
from apps.notifications.models import Notification
from apps.core.utils import log_audit
from apps.core.notifications import send_qms_email

User = get_user_model()

class Command(BaseCommand):
    help = "Run plant-wide automated Quality Management System (QMS) health check and daily compliance scan."

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-digest',
            action='store_true',
            help='Dispatch a styled HTML Daily Compliance Digest email to QA Managers & Super Admins.'
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        send_digest = options.get('send_digest', False)
        self.stdout.write(self.style.NOTICE(f"=== Starting QMS Plant Compliance Health Check [{today}] ==="))

        # 1. Check Overdue Actions
        overdue_qs = Action.objects.filter(
            due_date__lt=today,
            status__in=[Action.Status.OPEN, Action.Status.IN_PROGRESS, Action.Status.PENDING_VERIFICATION]
        )
        overdue_count = overdue_qs.count()
        for act in overdue_qs:
            act.status = Action.Status.OVERDUE
            act.save(update_fields=['status'])
            Notification.create_notification(
                recipient=act.assigned_to,
                title=f"⚠️ OVERDUE ACTION: {act.action_number}",
                message=f"Action '{act.title}' was due on {act.due_date}. Immediate action required!",
                link=f"/actions/{act.id}/"
            )
        self.stdout.write(self.style.SUCCESS(f"[Actions] {overdue_count} actions marked OVERDUE and notifications sent."))

        # 2. Metrology & Equipment Calibration Status Scan
        active_equipment = Equipment.objects.exclude(status=Equipment.Status.OUT_OF_SERVICE)
        status_updated = 0
        expired_count = 0
        due_soon_count = 0

        for eq in active_equipment:
            old_status = eq.status
            eq.update_status()
            if eq.status != old_status:
                eq.save(update_fields=['status'])
                status_updated += 1
            if eq.status == Equipment.Status.EXPIRED:
                expired_count += 1
            elif eq.status == Equipment.Status.DUE_SOON:
                due_soon_count += 1

        qa_leaders = list(User.objects.filter(role__in=[User.Role.QA_MANAGER, User.Role.SUPER_ADMIN], is_active=True))
        qa_emails = [l.email for l in qa_leaders if l.email]

        if expired_count > 0:
            for leader in qa_leaders:
                Notification.create_notification(
                    recipient=leader,
                    title=f"🚨 Metrology Alert: {expired_count} Instruments Expired",
                    message=f"There are {expired_count} measuring instruments with expired calibration certificates. Quarantine or recalibrate immediately!",
                    link="/calibration/"
                )
        self.stdout.write(self.style.SUCCESS(f"[Calibration] Updated {status_updated} instruments. Expired: {expired_count}, Due <30d: {due_soon_count}."))

        # 3. Training Certification Validity Scan
        expired_training = TrainingRecord.objects.filter(
            expiry_date__lt=today
        ).count()
        self.stdout.write(self.style.SUCCESS(f"[Training] {expired_training} training qualifications are currently expired."))

        # 4. Upcoming Internal Audits (Next 7 Days)
        next_week = today + timezone.timedelta(days=7)
        upcoming_audits = AuditPlan.objects.filter(
            audit_date__gte=today,
            audit_date__lte=next_week,
            status=AuditPlan.Status.SCHEDULED
        )
        for audit in upcoming_audits:
            Notification.create_notification(
                recipient=audit.lead_auditor,
                title=f"📅 Upcoming Audit: {audit.audit_number}",
                message=f"Audit '{audit.audit_title}' is scheduled on {audit.audit_date}.",
                link=f"/audits/{audit.id}/"
            )
        self.stdout.write(self.style.SUCCESS(f"[Audits] {upcoming_audits.count()} upcoming audit alerts dispatched."))

        # 5. Optional Email Digest Dispatch
        total_open_ncrs = NCR.objects.exclude(status=NCR.Status.CLOSED).count()
        if send_digest and qa_emails:
            context = {
                'check_date': today.strftime("%d %B %Y"),
                'total_open_ncrs': total_open_ncrs,
                'overdue_actions_count': overdue_count,
                'expired_calib_count': expired_count,
                'due_calib_count': due_soon_count,
                'expired_training_count': expired_training,
                'upcoming_audits_count': upcoming_audits.count(),
            }
            email_sent = send_qms_email(
                subject=f"Plant Quality Compliance Digest - {today}",
                template_name="emails/compliance_daily_digest.html",
                context=context,
                recipient_list=qa_emails
            )
            if email_sent:
                self.stdout.write(self.style.SUCCESS(f"[Email Digest] Dispatched daily compliance report to {len(qa_emails)} recipients."))

        # 6. Audit Log Record
        log_audit(
            user=None,
            action='UPDATE',
            module='HEALTH_CHECK',
            record_id='CRON-DAILY',
            record_name='Automated Quality Health Check',
            notes=f"Overdue Actions: {overdue_count}, Expired Calibration: {expired_count}, Expired Training: {expired_training}, Digest: {send_digest}"
        )

        self.stdout.write(self.style.SUCCESS("=== QMS Health Check Completed Successfully ==="))
