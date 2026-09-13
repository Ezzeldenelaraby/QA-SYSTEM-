from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from apps.departments.models import Department
from apps.processes.models import Process
from apps.documents.models import Document, DocumentRevision
from apps.risks.models import Risk
from apps.objectives.models import QualityObjective, ObjectiveMeasurement
from apps.ncr.models import NCR, FiveWhysAnalysis, FishboneCause
from apps.capa.models import CAPA
from apps.actions.models import Action
from apps.audits.models import AuditPlan, AuditChecklistItem, AuditFinding
from apps.inspections.models import Inspection, InspectionItem
from apps.calibration.models import Equipment
from apps.training.models import Course, TrainingRecord
from apps.management_review.models import ManagementReviewMeeting
from apps.notifications.models import Notification
from apps.core.models import SystemSetting

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds realistic demo industrial manufacturing data for QMS Hub'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding QMS Hub demo data..."))

        # 1. System Settings
        settings = SystemSetting.get_settings()
        settings.company_name = "Apex Precision Dynamics Industrial Ltd."
        settings.calibration_alert_days = 30
        settings.risk_high_threshold = 10
        settings.risk_critical_threshold = 15
        settings.save()

        # 2. Departments
        departments_data = [
            ("QA", "Quality Assurance", "Quality management, standards compliance, CAPA and system audits."),
            ("QC", "Quality Control", "Shop-floor inspections, receiving quality, testing and measurement lab."),
            ("PROD", "Production & Machining", "CNC machining, metal forming, fabrication, and cleanroom assembly."),
            ("MAINT", "Maintenance & Facilities", "Preventive and corrective maintenance of machine tools and utilities."),
            ("ENG", "Process & Tooling Engineering", "Process optimization, drawings, CAM programming, and cycle times."),
            ("WH", "Warehouse & Logistics", "Raw material storage, inventory staging, and finished product shipping."),
            ("SC", "Supply Chain & Procurement", "Vendor qualification, supplier evaluation, and raw material procurement."),
            ("HR", "Human Resources & Training", "Employee competencies, training matrix, and occupational health."),
            ("MGT", "Executive Management", "Leadership, quality objectives, management reviews, and strategic resources."),
        ]

        depts = {}
        for code, name, desc in departments_data:
            dept, _ = Department.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'active': True}
            )
            depts[code] = dept

        # 3. Users
        users_data = [
            ("admin", "Admin@123456", "admin@apexprecision.com", "John", "SuperAdmin", User.Role.SUPER_ADMIN, depts["QA"], "Director of Quality & Systems", True),
            ("sarah_qa", "Sarah@123456", "sarah.qa@apexprecision.com", "Sarah", "Jenkins", User.Role.QA_MANAGER, depts["QA"], "QA & Compliance Manager", False),
            ("omar_eng", "Omar@123456", "omar.eng@apexprecision.com", "Omar", "Hassan", User.Role.QA_ENGINEER, depts["QA"], "Senior Quality Engineer", False),
            ("tariq_qc", "Tariq@123456", "tariq.qc@apexprecision.com", "Tariq", "Mansour", User.Role.QC_INSPECTOR, depts["QC"], "Lead Metrology & QC Inspector", False),
            ("marcus_prod", "Marcus@123456", "marcus.p@apexprecision.com", "Marcus", "Vance", User.Role.PRODUCTION_MANAGER, depts["PROD"], "Production Operations Head", False),
            ("elena_auditor", "Elena@123456", "elena.a@apexprecision.com", "Elena", "Rostova", User.Role.AUDITOR, depts["QA"], "Certified ISO 9001 Lead Auditor", False),
            ("david_proc", "David@123456", "david.k@apexprecision.com", "David", "Kim", User.Role.PROCESS_OWNER, depts["ENG"], "Machining Process Owner", False),
            ("samir_emp", "Samir@123456", "samir.e@apexprecision.com", "Samir", "Zaki", User.Role.EMPLOYEE, depts["PROD"], "CNC Machine Operator", False),
        ]

        users = {}
        for uname, pwd, email, first, last, role, dept, title, is_super in users_data:
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': role,
                    'department': dept,
                    'job_title': title,
                    'is_staff': is_super or (role in [User.Role.SUPER_ADMIN, User.Role.QA_MANAGER]),
                    'is_superuser': is_super,
                }
            )
            if created or not user.check_password(pwd):
                user.set_password(pwd)
                user.save()
            users[uname] = user

        # Set department managers
        depts["QA"].manager = users["sarah_qa"]
        depts["QA"].save()
        depts["QC"].manager = users["tariq_qc"]
        depts["QC"].save()
        depts["PROD"].manager = users["marcus_prod"]
        depts["PROD"].save()

        # 4. Manufacturing Processes
        processes_data = [
            ("PRC-CNC-001", "CNC 5-Axis Precision Machining", depts["PROD"], users["david_proc"],
             "Subtractive high-speed machining of aerospace aluminum alloys and titanium alloy billets.",
             "Raw material bar stock, aerospace cad/cam models, cutting tools, synthetic coolants.",
             "Machined precision components, inspection dimensional reports, metal chips.",
             "Hermle C42U 5-Axis CNC Mill, Haas VF-4SS Vertical Machining Center.",
             "Kennametal solid carbide endmills, Sandvik indexable face mills, hydraulic vises.",
             "Spindle Speed: 12000 RPM, Feed: 3500 mm/min, Coolant Concentration: 8.5%, Tool Runout < 0.005mm.",
             "First-off dimensional check, Bore diameter air-gage check, Tool wear optical inspection.",
             "Quality Gate 1: First Article Inspection (FAI) approval before batch production release."),
            ("PRC-HT-002", "Vacuum Heat Treatment & Quenching", depts["PROD"], users["marcus_prod"],
             "Thermal processing to achieve specified grain structure, tensile strength, and core hardness.",
             "Machined alloy components, nitrogen/argon inert gas, quench oil.",
             "Heat-treated components, furnace heat-run temperature charts, hardness test coupons.",
             "Ipsen TurboTreater Vacuum Furnace, Automated Nitrogen Quench Vessel.",
             "Type-K calibrated thermocouples, Rockwell hardness indenters.",
             "Austenitizing Temp: 1040°C ± 5°C, Vacuum Level < 10^-3 mbar, Cooling rate > 25°C/sec.",
             "Core Rockwell C hardness (HRC 42-45), Microstructure grain size ASTM E112 check.",
             "Quality Gate 2: Tensile coupon destructive testing and metallurgical sign-off."),
            ("PRC-FIN-003", "Sulfuric Acid Anodizing & Passivation", depts["PROD"], users["omar_eng"],
             "Electrolytic passivation process for corrosion resistance, surface hardness, and wear endurance.",
             "Cleaned parts, deionized water, sulfuric acid electrolyte, nickel acetate seal.",
             "Anodized components (Type II / Type III hardcoat), salt spray coupons.",
             "Automated 12-tank plating line, 24V 3000A DC rectifier, DI water plant.",
             "Titanium racks, pH meters, eddy current coating thickness gages.",
             "Bath Temp: 20°C ± 1°C, Current Density: 1.5 A/dm2, Coating Thickness: 25 - 35 µm.",
             "Coating thickness eddy-current testing, Adhesion tape test ASTM D3359.",
             "Quality Gate 3: Visual inspection under 1000 lux illumination and coating thickness verification."),
            ("PRC-ASM-004", "Cleanroom Final Assembly & Pressure Test", depts["PROD"], users["marcus_prod"],
             "Integration of valve bodies, O-ring seals, springs, and digital actuators followed by helium leak testing.",
             "Anodized bodies, Viton seals, precision springs, servo actuators.",
             "Tested sub-assemblies, serialized certificate of conformity, blister packaging.",
             "Pfeiffer Helium Mass Spectrometer Leak Detector, Digital Torque Screwdrivers.",
             "Class 10,000 ISO 7 Cleanroom benches, anti-static ESD wrist straps.",
             "Helium background leak rate < 1x10^-8 mbar.l/s, Fastener Torque: 4.5 Nm ± 0.2 Nm.",
             "100% helium envelope leak test, 100% electrical actuator sweep test.",
             "Quality Gate 4: Final packaging seal verification and serialized COC generation."),
        ]

        processes = {}
        for code, name, dept, owner, desc, inp, outp, eq, tools, params, pts, gates in processes_data:
            proc, _ = Process.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'department': dept,
                    'process_owner': owner,
                    'description': desc,
                    'inputs': inp,
                    'outputs': outp,
                    'equipment': eq,
                    'tools': tools,
                    'parameters': params,
                    'inspection_points': pts,
                    'quality_gates': gates,
                    'status': Process.Status.ACTIVE
                }
            )
            processes[code] = proc

        # 5. Controlled Documents
        docs_data = [
            ("QM-001", "Apex Quality Management System Manual", Document.DocType.MANUAL, depts["QA"], None, "03",
             users["sarah_qa"], users["omar_eng"], users["sarah_qa"], users["admin"], Document.Status.APPROVED,
             "Annual review and update of ISO 9001:2015 / AS9100 quality policy statements."),
            ("SOP-CNC-001", "Standard Operating Procedure: 5-Axis CNC Setup & First Article", Document.DocType.PROCEDURE, depts["PROD"], processes["PRC-CNC-001"], "02",
             users["david_proc"], users["david_proc"], users["omar_eng"], users["sarah_qa"], Document.Status.APPROVED,
             "Added requirement for digital air-gage verification on critical bores."),
            ("WI-QC-014", "Work Instruction: Optical & CMM Automated Inspection", Document.DocType.WORK_INSTRUCTION, depts["QC"], processes["PRC-CNC-001"], "01",
             users["tariq_qc"], users["tariq_qc"], users["omar_eng"], users["sarah_qa"], Document.Status.APPROVED,
             "Initial release for automated CMM routine execution."),
            ("SOP-QA-004", "Control of Nonconforming Outputs & 8D / CAPA Procedure", Document.DocType.PROCEDURE, depts["QA"], None, "04",
             users["omar_eng"], users["omar_eng"], users["sarah_qa"], users["admin"], Document.Status.APPROVED,
             "Standardized root cause 5-Why and Fishbone category definitions."),
            ("SOP-CAL-002", "Calibration and Measurement Equipment Control Procedure", Document.DocType.PROCEDURE, depts["QC"], None, "02",
             users["tariq_qc"], users["tariq_qc"], users["omar_eng"], users["sarah_qa"], Document.Status.APPROVED,
             "Updated tolerance guardbanding and alert triggers for expired instruments."),
            ("FORM-QC-008", "Receiving Material Inspection Checklist & Certificate", Document.DocType.FORM, depts["QC"], None, "01",
             users["tariq_qc"], users["tariq_qc"], users["omar_eng"], None, Document.Status.UNDER_REVIEW,
             "Drafted new digital checklist for incoming bar stock heat lot verification."),
        ]

        docs = {}
        for num, title, dtype, dept, proc, rev, owner, prep, rev_by, app_by, stat, reason in docs_data:
            doc, _ = Document.objects.get_or_create(
                document_number=num,
                defaults={
                    'title': title,
                    'document_type': dtype,
                    'department': dept,
                    'process': proc,
                    'revision_number': rev,
                    'issue_date': timezone.now().date() - timedelta(days=90),
                    'effective_date': timezone.now().date() - timedelta(days=80),
                    'review_date': timezone.now().date() + timedelta(days=280),
                    'owner': owner,
                    'prepared_by': prep,
                    'reviewed_by': rev_by,
                    'approved_by': app_by,
                    'status': stat,
                    'revision_reason': reason,
                    'notes': "Official controlled document in QMS Hub repository."
                }
            )
            docs[num] = doc
            # Seed a historical revision for QM-001 and SOP-CNC-001
            if rev in ["02", "03", "04"]:
                DocumentRevision.objects.get_or_create(
                    document=doc,
                    revision_number="01",
                    defaults={
                        'revision_reason': "Initial release and baseline certification.",
                        'approved_by': users["admin"],
                        'approved_at': timezone.now() - timedelta(days=365),
                        'created_by': users["omar_eng"]
                    }
                )

        # 6. Risk Register
        risks_data = [
            ("RSK-2026-0001", processes["PRC-CNC-001"], depts["PROD"],
             "CNC High-Pressure Coolant bacterial contamination leading to premature tool failure and out-of-spec surface finish.",
             "Lack of automated biocidal monitoring and bi-weekly refractometer skimming checks.",
             "Tool chatter, rough surface Ra > 1.6 um on aerospace flanges, scrapping expensive parts ($12,000 lot).",
             "Manual weekly refractometer check log sheet.",
             3, 4, users["david_proc"], timezone.now().date() + timedelta(days=15), Risk.Status.MITIGATING,
             "Install digital automated coolant dosing and pH inline telemetry system."),
            ("RSK-2026-0002", processes["PRC-HT-002"], depts["PROD"],
             "Furnace thermocouple thermal drift causing undetected under-tempering and brittle component failure in field.",
             "Thermocouple aging and delayed secondary calibration check.",
             "Catastrophic hydraulic manifold burst under operational load, customer safety recall.",
             "Quarterly 9-point temperature uniformity survey (TUS) per AMS2750.",
             2, 5, users["marcus_prod"], timezone.now().date() + timedelta(days=30), Risk.Status.CONTROLLED,
             "Redundant dual-channel Class 1 thermocouples with automatic alarm deviation trigger."),
            ("RSK-2026-0003", processes["PRC-FIN-003"], depts["PROD"],
             "Anodize bath temperature spike during summer ambient heat exceeding 24°C, causing soft spongy coating.",
             "Aging chiller compressor capacity degradation.",
             "Loss of corrosion protection, rejection by aerospace customer, re-anodizing cycle cost.",
             "Chiller thermostat set to 19°C.",
             4, 4, users["omar_eng"], timezone.now().date() - timedelta(days=5), Risk.Status.OPEN,
             "Dual-redundant 50kW titanium plate heat exchanger chiller overhaul."),
            ("RSK-2026-0004", processes["PRC-ASM-004"], depts["PROD"],
             "Operator ESD strap ground fault discharging electrostatic voltage into digital servo valve microcontrollers.",
             "Worn wrist strap cables and missed daily ESD bench testing.",
             "Latent component failure in flight control actuators after 50 operating hours.",
             "Daily ESD turnstile gate log.",
             2, 4, users["marcus_prod"], timezone.now().date() + timedelta(days=45), Risk.Status.CONTROLLED,
             "Continuous real-time wrist strap grounding monitor with bench lockouts."),
            ("RSK-2026-0005", processes["PRC-CNC-001"], depts["PROD"],
             "Incorrect CNC G-code program uploaded to machine controller without revision verification.",
             "Manual USB flash drive transfer of CAM programs by machine operators.",
             "Tool collision with fixture table, machine spindle replacement cost > $45,000.",
             "Operator visually checks program header revision number against traveler.",
             3, 5, users["david_proc"], timezone.now().date() + timedelta(days=10), Risk.Status.MITIGATING,
             "Deploy DNC network direct locked transfer with barcode traveler scan."),
        ]

        risks = {}
        for rid, proc, dept, desc, cause, cons, ctrl, lik, sev, resp, due, stat, mit in risks_data:
            risk, _ = Risk.objects.get_or_create(
                risk_id=rid,
                defaults={
                    'process': proc,
                    'department': dept,
                    'description': desc,
                    'cause': cause,
                    'potential_consequence': cons,
                    'existing_control': ctrl,
                    'likelihood': lik,
                    'severity': sev,
                    'responsible_person': resp,
                    'due_date': due,
                    'status': stat,
                    'effectiveness': mit,
                    'evidence': "FMEA Risk Analysis Matrix documented."
                }
            )
            risks[rid] = risk

        # 7. Quality Objectives & Monthly Trends
        objs_data = [
            ("OBJ-2026-01", "CNC Machining Scrap Rate Reduction", depts["PROD"], processes["PRC-CNC-001"],
             "Reduce precision machining material and rework scrap rate to world-class manufacturing benchmark.",
             "Scrap Percentage of Total Machined Lots", "Monthly scrap weight vs raw input ratio",
             Decimal("3.80"), Decimal("1.20"), Decimal("1.45"), "%",
             timezone.now().date() - timedelta(days=180), timezone.now().date() + timedelta(days=185),
             users["david_proc"], QualityObjective.Status.ON_TRACK),
            ("OBJ-2026-02", "First Pass Yield (FPY) at Final Assembly", depts["PROD"], processes["PRC-ASM-004"],
             "Achieve 98.5% or higher First Pass Yield on assembled actuator valves without teardown.",
             "Final Test First Pass Yield", "Passed units on first test / total tested units * 100",
             Decimal("92.50"), Decimal("98.50"), Decimal("97.80"), "%",
             timezone.now().date() - timedelta(days=180), timezone.now().date() + timedelta(days=185),
             users["marcus_prod"], QualityObjective.Status.ON_TRACK),
            ("OBJ-2026-03", "Supplier On-Time & In-Spec Delivery (OTIF)", depts["SC"], None,
             "Ensure qualified tier-1 raw material suppliers meet on-time delivery with full cert conformity.",
             "Supplier OTIF Score", "Compliant shipments delivered on or before dock promise date",
             Decimal("84.00"), Decimal("96.00"), Decimal("89.50"), "%",
             timezone.now().date() - timedelta(days=180), timezone.now().date() + timedelta(days=185),
             users["sarah_qa"], QualityObjective.Status.AT_RISK),
            ("OBJ-2026-04", "Customer Returns & RMA Rate", depts["QA"], None,
             "Maintain zero critical escapes and reduce customer warranty returns below 150 PPM.",
             "Customer Defect PPM", "Returned defective parts / total shipped million parts",
             Decimal("420.00"), Decimal("150.00"), Decimal("135.00"), "PPM",
             timezone.now().date() - timedelta(days=180), timezone.now().date() + timedelta(days=185),
             users["omar_eng"], QualityObjective.Status.ACHIEVED),
        ]

        objectives = {}
        for code, name, dept, proc, desc, kpi, mm, base, target, actual, unit, sdate, ddate, resp, stat in objs_data:
            obj, _ = QualityObjective.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'department': dept,
                    'process': proc,
                    'description': desc,
                    'kpi': kpi,
                    'measurement_method': mm,
                    'baseline': base,
                    'target': target,
                    'actual_result': actual,
                    'unit': unit,
                    'start_date': sdate,
                    'due_date': ddate,
                    'responsible_person': resp,
                    'status': stat,
                    'notes': "Tracked monthly in executive quality dashboard."
                }
            )
            objectives[code] = obj

            # Seed 5 months of historical measurements
            month_vals = [
                (base, 5),
                (base - Decimal("0.5"), 4),
                (base - Decimal("1.1"), 3),
                (base - Decimal("1.8"), 2),
                (actual, 1),
            ]
            for val, months_ago in month_vals:
                pdate = timezone.now().date() - timedelta(days=months_ago * 30)
                ObjectiveMeasurement.objects.get_or_create(
                    objective=obj,
                    period_date=pdate,
                    defaults={'value': val, 'notes': f'Historical monthly metric for {pdate:%B %Y}', 'recorded_by': resp}
                )

        # 8. NCR Management with 5-Whys and Fishbone
        ncr_data = [
            ("NCR-2026-0001", timezone.now().date() - timedelta(days=22), depts["PROD"], processes["PRC-CNC-001"],
             "Titanium Aerospace Flange P/N TF-9920", "LOT-2026-0819", users["tariq_qc"], NCR.Source.INSPECTION,
             "Internal bore diameter measured at 48.075 mm, exceeding drawing upper specification limit of 48.000 ± 0.025 mm.",
             "Drawing TF-9920 Rev C, Zone D-4 specifies diameter 48.000 +0.025/-0.000 mm.",
             "CMM report #CMM-8812 verified on 14 out of 50 sampled parts.",
             NCR.Classification.MAJOR, NCR.Severity.HIGH,
             "Immediate red-tag quarantine of entire batch of 50 flanges into secure MRB cage.",
             "100% sort of upstream and downstream inventory; machine spindle paused pending tool calibration.",
             "Severe flank wear on indexable boring insert due to coolant flow diversion, undetected by operator during night shift.",
             users["david_proc"], timezone.now().date() - timedelta(days=5), NCR.Status.CLOSED,
             "Tool wear sensor calibrated, replacement boring bar installed, FAI passed with bore 48.012 mm.",
             users["sarah_qa"]),

            ("NCR-2026-0002", timezone.now().date() - timedelta(days=8), depts["PROD"], processes["PRC-FIN-003"],
             "Hydraulic Actuator Piston Cylinder P/N HA-440", "LOT-2026-0902", users["tariq_qc"], NCR.Source.PRODUCTION,
             "Anodize layer peeling and blistering along sharp chamfer edges during adhesion cross-hatch tape test.",
             "MIL-A-8625F Type III Class 1 specification: Zero delamination or flaking permitted.",
             "Optical microscopy photo showing 150 um delamination patch on sample #3.",
             NCR.Classification.MAJOR, NCR.Severity.HIGH,
             "Hold shipment of 200 cylinders. Chemical strip and prepare test bath for surface re-cleaning.",
             "Audit current alkaline cleaner degreasing temperature and rinse bath conductivity.",
             "Silicate residue carry-over from contaminated hot rinse bath tank #4.",
             users["omar_eng"], timezone.now().date() + timedelta(days=6), NCR.Status.CORRECTIVE_ACTION,
             "", None),

            ("NCR-2026-0003", timezone.now().date() - timedelta(days=3), depts["QC"], processes["PRC-ASM-004"],
             "High-Pressure Control Valve Assembly P/N VLV-100", "LOT-2026-0910", users["samir_emp"], NCR.Source.INSPECTION,
             "Helium leak detector indicated micro-leakage rate of 4.2 x 10^-6 mbar.l/s at port B seal interface.",
             "Test Spec TS-VLV-01: Maximum permissible helium leakage rate 1.0 x 10^-7 mbar.l/s.",
             "Mass spectrometer calibration certificate and log graph showing leak spike.",
             NCR.Classification.CRITICAL, NCR.Severity.CRITICAL,
             "Assembly halted immediately; 25 completed units isolated from packaging area.",
             "Inspect incoming lot of Viton fluoropolymer O-rings for parting line flash.",
             "", users["marcus_prod"], timezone.now().date() + timedelta(days=4), NCR.Status.ROOT_CAUSE_ANALYSIS,
             "", None),

            ("NCR-2026-0004", timezone.now().date() - timedelta(days=1), depts["WH"], None,
             "Raw Aluminum 7075-T651 Round Bar 120mm Dia", "HEAT-88291-A", users["tariq_qc"], NCR.Source.SUPPLIER,
             "Mill test report missing ASTM ultrasonic inspection certificate and hardness report.",
             "Procurement Specification PS-AL-7075 Clause 4.2: Mandatory Level A ultrasonic testing.",
             "Physical inspection upon receiving dock. Vendor delivery slip lacks certified lab stamp.",
             NCR.Classification.MINOR, NCR.Severity.MEDIUM,
             "Material quarantined in receiving inspection staging bay with yellow caution hold ribbon.",
             "Issue formal supplier discrepancy notice to metal distributor.",
             "", users["sarah_qa"], timezone.now().date() + timedelta(days=7), NCR.Status.OPEN,
             "", None),
        ]

        ncrs = {}
        for num, dt, dept, proc, prod, lot, rep, src, desc, req, evid, clf, sev, imm, cont, rc, resp, due, stat, vnotes, vby in ncr_data:
            ncr, _ = NCR.objects.get_or_create(
                ncr_number=num,
                defaults={
                    'date': dt,
                    'department': dept,
                    'process': proc,
                    'product': prod,
                    'batch_lot': lot,
                    'reported_by': rep,
                    'source': src,
                    'description': desc,
                    'requirement': req,
                    'evidence': evid,
                    'classification': clf,
                    'severity': sev,
                    'immediate_correction': imm,
                    'containment_action': cont,
                    'root_cause_summary': rc,
                    'responsible_person': resp,
                    'due_date': due,
                    'status': stat,
                    'verification_notes': vnotes,
                    'verified_by': vby,
                    'closed_date': timezone.now().date() - timedelta(days=1) if stat == NCR.Status.CLOSED else None,
                }
            )
            ncrs[num] = ncr

        # Seed 5-Whys for NCR-2026-0001
        FiveWhysAnalysis.objects.get_or_create(
            ncr=ncrs["NCR-2026-0001"],
            defaults={
                'problem_statement': "Titanium Flange internal bore oversize by +0.050 mm.",
                'why_1': "The finish boring bar cut deeper into the workpiece than programmed.",
                'why_2': "The carbide insert experienced severe thermal wear and edge buildup.",
                'why_3': "High-pressure coolant was not hitting the cutting tip directly.",
                'why_4': "The flexible coolant nozzle shifted during chip evacuation earlier in the run.",
                'why_5': "The machine lacked rigid targeted manifold nozzles and automated tool wear monitoring.",
                'root_cause_conclusion': "Inadequate coolant nozzle rigidity combined with absence of automated spindle load monitoring for tool degradation."
            }
        )

        # Seed Fishbone Causes for NCR-2026-0001
        fishbone_items = [
            (FishboneCause.Category.MAN, "Night shift operator skipped midway tool flank inspection.", False),
            (FishboneCause.Category.MACHINE, "Movable flexible coolant pipe vibrated loose under 70 bar pump pressure.", True),
            (FishboneCause.Category.METHOD, "Setup sheet did not mandate rigid toolholder nozzle lock inspection.", True),
            (FishboneCause.Category.MATERIAL, "Titanium Ti-6Al-4V Grade 5 alloy exhibits high abrasiveness and heat retention.", False),
            (FishboneCause.Category.MEASUREMENT, "Bore measurement was only scheduled at start and end of 50-part batch.", False),
            (FishboneCause.Category.ENVIRONMENT, "Ambient shop floor temperature variation of 6°C during night transition.", False),
        ]
        for cat, text, is_p in fishbone_items:
            FishboneCause.objects.get_or_create(
                ncr=ncrs["NCR-2026-0001"],
                category=cat,
                cause_description=text,
                defaults={'is_primary': is_p}
            )

        # 9. CAPA Management
        capas_data = [
            ("CAPA-2026-0001", "Elimination of Bore Dimensional Out-of-Tolerance via Rigid Tooling & Inline Probing",
             CAPA.Source.NCR, ncrs["NCR-2026-0001"], None, risks["RSK-2026-0001"],
             "Recurring titanium bore deviations caused by coolant nozzle displacement and tool wear.",
             "Flexible coolant nozzles drift under 70-bar pulsating pressure, causing intermittent thermal shock to boring inserts.",
             "1. Retrofit all 5-Axis CNC spindles with rigid stainless-steel internally-ported targeted coolant blocks.\n2. Implement Renishaw RMP60 touch probe macro to measure bore every 5 parts automatically.",
             "Update CNC setup validation SOP-CNC-001 to mandate rigid nozzle torque check across all machines.",
             users["david_proc"], timezone.now().date() - timedelta(days=20), timezone.now().date() + timedelta(days=10),
             timezone.now().date() - timedelta(days=2), "Statistical Process Control (SPC) Cpk evaluation on next 5 production lots.",
             "Evaluated 250 parts across 5 consecutive lots: Bore Cpk improved from 1.08 to 1.84 with zero dimensional defects.",
             users["sarah_qa"], CAPA.Status.CLOSED),

            ("CAPA-2026-0002", "Anodize Rinse Tank Contamination Prevention & Conductivity Interlocks",
             CAPA.Source.NCR, ncrs["NCR-2026-0002"], None, None,
             "Anodizing coating flaking and adhesion failure due to silicate carryover in rinse baths.",
             "Rinse bath overflow rate was manually throttled to conserve water, allowing dissolved solids to concentrate.",
             "Install automated inline continuous conductivity sensor with solenoid fresh DI water flush trigger.",
             "Deploy rinse water standard operating limit in daily lab log sheet with automated SCADA lockout.",
             users["omar_eng"], timezone.now().date() - timedelta(days=7), timezone.now().date() + timedelta(days=25),
             None, "Weekly cross-hatch adhesion testing on 10 consecutive production racks.",
             "", None, CAPA.Status.IMPLEMENTATION),
        ]

        capas = {}
        for num, title, src, ncr, fnd, rsk, desc, rc, ca, pa, resp, sdate, ddate, cdate, vmeth, eff, vby, stat in capas_data:
            capa, _ = CAPA.objects.get_or_create(
                capa_number=num,
                defaults={
                    'title': title,
                    'source': src,
                    'related_ncr': ncr,
                    'related_finding': fnd,
                    'related_risk': rsk,
                    'description': desc,
                    'root_cause': rc,
                    'corrective_action': ca,
                    'preventive_action': pa,
                    'responsible_person': resp,
                    'start_date': sdate,
                    'due_date': ddate,
                    'completion_date': cdate,
                    'verification_method': vmeth,
                    'effectiveness_result': eff,
                    'verified_by': vby,
                    'status': stat,
                    'evidence': "Engineering change order ECO-2026-04 and validation run test records attached."
                }
            )
            capas[num] = capa

        # 10. Central Action Management
        actions_data = [
            ("ACT-2026-0001", "Install Stainless Internal Coolant Manifold on CNC Mill #2",
             "Procure and mount hardened coolant manifold to guarantee permanent tool tip aim.",
             Action.SourceType.CAPA, capas["CAPA-2026-0001"].capa_number, depts["PROD"], processes["PRC-CNC-001"],
             users["david_proc"], users["sarah_qa"], Action.Priority.HIGH,
             timezone.now().date() - timedelta(days=15), timezone.now().date() - timedelta(days=3),
             timezone.now().date() - timedelta(days=4), Action.Status.COMPLETED,
             "Installed and pressure-tested at 80 bar. Aim verified with laser pointer.", users["sarah_qa"]),

            ("ACT-2026-0002", "Configure Renishaw Bore Probing Routine in G-Code Macro",
             "Program in-process macro O9012 to stop machine if bore dimension drifts past ±0.015 mm.",
             Action.SourceType.CAPA, capas["CAPA-2026-0001"].capa_number, depts["ENG"], processes["PRC-CNC-001"],
             users["david_proc"], users["omar_eng"], Action.Priority.MEDIUM,
             timezone.now().date() - timedelta(days=12), timezone.now().date() - timedelta(days=2),
             timezone.now().date() - timedelta(days=2), Action.Status.COMPLETED,
             "Macro O9012 simulated and activated in CNC controller memory.", users["omar_eng"]),

            ("ACT-2026-0003", "Order Automated Conductivity Sensor for Anodize Rinse Tank #4",
             "Purchase Thornton M300 conductivity transmitter and valve actuator.",
             Action.SourceType.NCR, ncrs["NCR-2026-0002"].ncr_number, depts["QA"], processes["PRC-FIN-003"],
             users["omar_eng"], users["sarah_qa"], Action.Priority.CRITICAL,
             timezone.now().date() - timedelta(days=5), timezone.now().date() - timedelta(days=1),
             None, Action.Status.OVERDUE,
             "PO issued to vendor, expedited delivery expected in 2 days.", None),

            ("ACT-2026-0004", "Calibrate Granite Surface Plate #3 in Quality Lab",
             "Conduct annual laser interferometer flatness audit for metrology surface table.",
             Action.SourceType.GENERIC, "CAL-SURF-03", depts["QC"], None,
             users["tariq_qc"], users["sarah_qa"], Action.Priority.MEDIUM,
             timezone.now().date() - timedelta(days=2), timezone.now().date() + timedelta(days=1),
             None, Action.Status.IN_PROGRESS,
             "", None),

            ("ACT-2026-0005", "Perform Supplier Audit on AeroAlloy Forgings Ltd.",
             "On-site ISO 9001 and raw material traceability verification.",
             Action.SourceType.AUDIT, "AUD-EXT-01", depts["QA"], None,
             users["elena_auditor"], users["sarah_qa"], Action.Priority.HIGH,
             timezone.now().date(), timezone.now().date() + timedelta(days=14),
             None, Action.Status.OPEN,
             "", None),

            ("ACT-2026-0006", "Update Cleanroom Glovebox Filter Differential Pressure Log",
             "Ensure daily HEPA filter DP manometer records are uploaded into QMS.",
             Action.SourceType.GENERIC, "HEPA-DP-01", depts["PROD"], processes["PRC-ASM-004"],
             users["samir_emp"], users["marcus_prod"], Action.Priority.LOW,
             timezone.now().date() - timedelta(days=4), timezone.now().date() + timedelta(days=5),
             None, Action.Status.IN_PROGRESS,
             "", None),
        ]

        for num, title, desc, stype, sid, dept, proc, asg, crt, prio, sdate, ddate, cdate, stat, evid, vby in actions_data:
            Action.objects.get_or_create(
                action_number=num,
                defaults={
                    'title': title,
                    'description': desc,
                    'source_type': stype,
                    'source_id': sid,
                    'department': dept,
                    'process': proc,
                    'assigned_to': asg,
                    'created_by': crt,
                    'priority': prio,
                    'start_date': sdate,
                    'due_date': ddate,
                    'completion_date': cdate,
                    'status': stat,
                    'evidence': evid,
                    'verification': "Verified compliant with procedure." if vby else "",
                    'verified_by': vby,
                }
            )

        # 11. Internal Audits
        audit_plan, _ = AuditPlan.objects.get_or_create(
            audit_number="AUD-2026-0001",
            defaults={
                'audit_title': "Internal Audit: CNC Machining & Heat Treatment Operations (ISO 9001 Clauses 7.1.5, 8.5)",
                'department': depts["PROD"],
                'process': processes["PRC-CNC-001"],
                'lead_auditor': users["elena_auditor"],
                'audit_date': timezone.now().date() - timedelta(days=14),
                'scope': "Shift 1 & 2 CNC production cells, tooling storage, and Ipsen vacuum furnace heat treatment.",
                'criteria': "ISO 9001:2015 Clauses 7.1.5 (Monitoring & Measuring Resources), 8.5.1 (Control of Production).",
                'status': AuditPlan.Status.CLOSED,
                'summary_notes': "Audit completed successfully. 1 Minor Nonconformity and 2 Opportunities for Improvement recorded."
            }
        )
        audit_plan.audit_team.add(users["omar_eng"])

        # Checklist Items
        checklists = [
            ("7.1.5.1", "Are monitoring and measuring resources calibrated and traceable to national/international standards?",
             "Gage stickers inspected on 12 micrometers and calipers across lines A & B.",
             AuditChecklistItem.Result.CONFORMITY, "All 12 instruments had valid calibration certificates and unbroken seal tags."),
            ("8.5.1.a", "Are documented work instructions available at work stations and accessible to operators?",
             "Sampled 4 machine consoles: SOP-CNC-001 Rev 02 visible on touchscreens.",
             AuditChecklistItem.Result.CONFORMITY, "Operators demonstrated retrieval of latest approved work instruction."),
            ("7.1.5.2", "Is equipment safeguarded from adjustments that would invalidate measurement results?",
             "Digital dial indicator on Station 3 lacked zero-lock password protection.",
             AuditChecklistItem.Result.NONCONFORMITY, "Operator was able to reset datum without supervisor key."),
            ("8.5.1.c", "Is suitable infrastructure and environment maintained for operation of processes?",
             "Oil mist collector on Mill #4 showing filter saturation warning light.",
             AuditChecklistItem.Result.OFI, "Recommend connecting filter pressure sensor to maintenance SCADA alert."),
        ]
        for clause, q, req, res, comm in checklists:
            AuditChecklistItem.objects.get_or_create(
                audit=audit_plan,
                iso_clause=clause,
                question=q,
                defaults={'requirement': req, 'result': res, 'comment': comm}
            )

        # Audit Finding
        AuditFinding.objects.get_or_create(
            finding_number=f"FND-{audit_plan.audit_number}-01",
            defaults={
                'audit': audit_plan,
                'finding_type': AuditFinding.FindingType.MINOR_NC,
                'description': "Digital height indicator gauge at Inspection Station 3 lacked adjustment lockout controls, allowing unverified datum recalibration.",
                'evidence': "Gauge S/N MIT-9921 observed being re-zeroed by line operator without master gage block re-validation.",
                'clause': "ISO 9001:2015 Clause 7.1.5.2.b",
                'responsible_person': users["tariq_qc"],
                'due_date': timezone.now().date() + timedelta(days=14),
                'status': AuditFinding.Status.IN_PROGRESS,
            }
        )

        # 12. Shop Floor Quality Inspections
        insp1, _ = Inspection.objects.get_or_create(
            inspection_number="INSP-2026-0001",
            defaults={
                'date': timezone.now().date() - timedelta(days=2),
                'process': processes["PRC-CNC-001"],
                'product': "Turbine Impeller Hub P/N TI-104",
                'batch_lot': "LOT-2026-0911",
                'machine': "Hermle C42U Mill #1",
                'inspector': users["tariq_qc"],
                'shift': Inspection.Shift.MORNING,
                'overall_result': Inspection.Result.OK,
                'comments': "First Article Inspection (FAI) complete. All 6 critical dimensions within drawing tolerances."
            }
        )
        insp1_items = [
            ("Outer Hub Diameter", "120.000 ± 0.015 mm", "120.008", "mm", InspectionItem.ItemResult.OK, "Measured with Mitutoyo Micrometer"),
            ("Bore Concentricity", "Max 0.008 mm TIR", "0.004", "mm", InspectionItem.ItemResult.OK, "Checked on air bearing rotary table"),
            ("Surface Roughness Ra", "Ra <= 0.8 um", "0.52", "um", InspectionItem.ItemResult.OK, "Mitutoyo Surftest SJ-210"),
        ]
        for name, spec, val, unit, res, comm in insp1_items:
            InspectionItem.objects.get_or_create(
                inspection=insp1,
                checkpoint_name=name,
                defaults={'specification': spec, 'measured_value': val, 'unit': unit, 'result': res, 'comment': comm}
            )

        insp2, _ = Inspection.objects.get_or_create(
            inspection_number="INSP-2026-0002",
            defaults={
                'date': timezone.now().date() - timedelta(days=1),
                'process': processes["PRC-CNC-001"],
                'product': "Titanium Aerospace Flange P/N TF-9920",
                'batch_lot': "LOT-2026-0912",
                'machine': "Haas VF-4SS Mill #2",
                'inspector': users["tariq_qc"],
                'shift': Inspection.Shift.AFTERNOON,
                'overall_result': Inspection.Result.NG,
                'comments': "Check failed on internal bore diameter. Part rejected (NG). NCR-2026-0001 referenced.",
                'linked_ncr': ncrs["NCR-2026-0001"]
            }
        )
        insp2_items = [
            ("Flange Thickness", "15.00 ± 0.05 mm", "15.01", "mm", InspectionItem.ItemResult.OK, "Verified with digital caliper"),
            ("Internal Bore Diameter", "48.000 +0.025/-0.000 mm", "48.075", "mm", InspectionItem.ItemResult.NG, "Oversize by +0.050 mm. Boring tool worn."),
            ("Bolt Circle Pitch", "85.00 ± 0.02 mm", "85.005", "mm", InspectionItem.ItemResult.OK, "CMM verified"),
        ]
        for name, spec, val, unit, res, comm in insp2_items:
            InspectionItem.objects.get_or_create(
                inspection=insp2,
                checkpoint_name=name,
                defaults={'specification': spec, 'measured_value': val, 'unit': unit, 'result': res, 'comment': comm}
            )

        # 13. Calibration Equipment
        equipment_data = [
            ("EQ-CAL-001", "Mitutoyo Digimatic Outside Micrometer 0-25mm", Equipment.Category.MICROMETER,
             "Mitutoyo", "293-240-30", "SN-8829101", depts["QC"], "Tool Crib #1 / Lab Bench 2",
             "0 - 25 mm", "± 0.001 mm", 12, timezone.now().date() - timedelta(days=120),
             "Accredited Metrology Lab ISO 17025", Equipment.Status.VALID),

            ("EQ-CAL-002", "Mitutoyo Electronic Digital Caliper 150mm", Equipment.Category.CALIPER,
             "Mitutoyo", "500-196-30", "SN-4410294", depts["PROD"], "CNC Mill Line Cell 1",
             "0 - 150 mm", "± 0.02 mm", 12, timezone.now().date() - timedelta(days=345),
             "Internal Metrology Lab", Equipment.Status.DUE_SOON),

            ("EQ-CAL-003", "Sturtevant Richmont Digital Torque Screwdriver", Equipment.Category.TORQUE_WRENCH,
             "Sturtevant", "DTC-50", "SN-TRQ-901", depts["PROD"], "Assembly Cleanroom Bench 4",
             "0.5 - 5.0 Nm", "± 1%", 6, timezone.now().date() - timedelta(days=210),
             "Sturtevant Authorized Service", Equipment.Status.EXPIRED),

            ("EQ-CAL-004", "WIKA Industrial Hydraulic Pressure Gauge 0-250 Bar", Equipment.Category.PRESSURE_GAUGE,
             "WIKA", "232.50", "SN-PG-5502", depts["MAINT"], "Vacuum Furnace Pressure Header",
             "0 - 250 bar", "± 1.0% F.S.", 12, timezone.now().date() - timedelta(days=60),
             "National Calibration Institute", Equipment.Status.VALID),

            ("EQ-CAL-005", "Zeiss CMM Touch Trigger Probe Head", Equipment.Category.CMM,
             "Carl Zeiss", "VAST XXT", "SN-ZSS-0982", depts["QC"], "Climate Controlled Metrology Lab",
             "3D Spatial Coordinates", "± 0.0008 mm", 12, timezone.now().date() - timedelta(days=350),
             "Zeiss Field Metrology Service", Equipment.Status.DUE_SOON),
        ]

        for eq_id, name, cat, mfr, mdl, sn, dept, loc, rng, acc, freq, ldate, prov, stat in equipment_data:
            Equipment.objects.get_or_create(
                equipment_id=eq_id,
                defaults={
                    'equipment_name': name,
                    'category': cat,
                    'manufacturer': mfr,
                    'model': mdl,
                    'serial_number': sn,
                    'department': dept,
                    'location': loc,
                    'measurement_range': rng,
                    'accuracy': acc,
                    'calibration_frequency_months': freq,
                    'last_calibration_date': ldate,
                    'calibration_provider': prov,
                    'status': stat,
                    'notes': "Official calibration master registered in metrology database."
                }
            )

        # 14. Training & Competencies
        courses_data = [
            ("TRN-ISO-01", "ISO 9001:2015 Requirements & QMS Fundamentals", Course.CourseType.QUALITY, None, docs["QM-001"], 24,
             "Overview of ISO 9001 quality management principles, process approach, and risk-based thinking."),
            ("TRN-CNC-02", "5-Axis Machine Setup & Tool Offset Verification", Course.CourseType.TECHNICAL, processes["PRC-CNC-001"], docs["SOP-CNC-001"], 12,
             "Hands-on training for Hermle 5-axis mill setup, fixture alignment, and probing routines."),
            ("TRN-MET-03", "Precision Measurement & GD&T Drawing Interpretation", Course.CourseType.QUALITY, None, docs["WI-QC-014"], 24,
             "Interpretation of ASME Y14.5 Geometric Dimensioning & Tolerancing symbols and micrometer practice."),
            ("TRN-8D-04", "Root Cause Analysis (5-Whys & Fishbone Diagramming)", Course.CourseType.QUALITY, None, docs["SOP-QA-004"], 12,
             "Systematic problem solving methodologies for shop floor deviations and CAPA investigations."),
        ]

        courses = {}
        for ccode, title, ctype, proc, doc, val, desc in courses_data:
            c, _ = Course.objects.get_or_create(
                code=ccode,
                defaults={
                    'title': title,
                    'course_type': ctype,
                    'related_process': proc,
                    'related_document': doc,
                    'validity_months': val,
                    'description': desc
                }
            )
            courses[ccode] = c

        # Training Records
        training_records = [
            (users["samir_emp"], courses["TRN-CNC-02"], "David Kim (Lead CAM Specialist)", timezone.now().date() - timedelta(days=60), TrainingRecord.Result.PASS, TrainingRecord.Competency.COMPETENT),
            (users["samir_emp"], courses["TRN-ISO-01"], "Sarah Jenkins (QA Manager)", timezone.now().date() - timedelta(days=180), TrainingRecord.Result.PASS, TrainingRecord.Competency.COMPETENT),
            (users["tariq_qc"], courses["TRN-MET-03"], "Mitutoyo Institute of Metrology", timezone.now().date() - timedelta(days=120), TrainingRecord.Result.PASS, TrainingRecord.Competency.COMPETENT),
            (users["omar_eng"], courses["TRN-8D-04"], "ASQ Certified Master Black Belt", timezone.now().date() - timedelta(days=90), TrainingRecord.Result.PASS, TrainingRecord.Competency.COMPETENT),
            (users["david_proc"], courses["TRN-8D-04"], "ASQ Certified Master Black Belt", timezone.now().date() - timedelta(days=90), TrainingRecord.Result.PASS, TrainingRecord.Competency.COMPETENT),
        ]
        for emp, course, trainer, tdate, res, comp in training_records:
            TrainingRecord.objects.get_or_create(
                employee=emp,
                course=course,
                defaults={
                    'trainer': trainer,
                    'training_date': tdate,
                    'result': res,
                    'competency_status': comp,
                    'notes': "Training validated and employee signed competency matrix."
                }
            )

        # 15. Management Review
        mr, _ = ManagementReviewMeeting.objects.get_or_create(
            meeting_number="MR-2026-0001",
            defaults={
                'title': "Annual Executive Management Review - QMS Performance & Strategic Direction",
                'meeting_date': timezone.now().date() - timedelta(days=10),
                'chairperson': users["admin"],
                'participants': "John SuperAdmin (Director of Quality), Sarah Jenkins (QA Manager), Marcus Vance (Production Head), Omar Hassan (Sr QA Engineer), David Kim (Tooling Head)",
                'status': ManagementReviewMeeting.Status.MINUTES_APPROVED,
                'general_summary': "The annual QMS review affirmed that Apex Precision's Quality Management System remains suitable, adequate, effective, and aligned with company strategic growth.",
                'inputs_previous_actions': "All 5 action items from Q3 Management Review completed satisfactorily.",
                'inputs_audit_results': "Internal audit AUD-2026-0001 completed with 1 minor finding, zero major nonconformities. Stage 2 Surveillance audit passed.",
                'inputs_customer_feedback': "Customer satisfaction index improved to 94.2%. On-time delivery OTIF standing at 89.5%.",
                'inputs_process_performance': "CNC Machining scrap rate reduced from 3.8% to 1.45%. Final Assembly First Pass Yield reached 97.8%.",
                'inputs_quality_objectives': "3 out of 4 Quality Objectives currently On Track or Achieved.",
                'inputs_ncr_capa_status': "Total 4 NCRs logged in period. CAPA-2026-0001 closed with proven Cpk improvement to 1.84.",
                'inputs_supplier_performance': "Tier-1 raw material suppliers maintained 96% conformance. 1 supplier discrepancy notice issued.",
                'inputs_risks_opportunities': "Risk register reviewed: Coolant contamination risk mitigated with rigid manifolds. Vacuum furnace sensors upgraded.",
                'inputs_resource_needs': "Need identified for additional CMM programmer to support expanding aerospace contracts.",
                'inputs_improvement_opportunities': "Deploy automated SPC data collection directly from CNC machines to QMS Hub database.",
                'outputs_decisions': "1. Approved capital expenditure budget for automated rinse tank conductivity monitoring.\n2. Mandate digital in-process probing across all new production part setups.",
                'outputs_resource_requirements': "Approved recruitment of 1 additional QC Metrology Inspector for Shift 2.",
                'outputs_improvement_projects': "QMS Hub digital shop floor inspection terminal rollout across Assembly Cells.",
            }
        )

        # 16. In-App Notifications
        notifs = [
            (users["david_proc"], "Action Assigned: Stainless Coolant Manifold", "You have been assigned action ACT-2026-0001 for CAPA-2026-0001.", "/actions/"),
            (users["omar_eng"], "Action OVERDUE: Conductivity Sensor Order", "Action ACT-2026-0003 is overdue. Please provide completion status.", "/actions/"),
            (users["sarah_qa"], "Document Approval Pending: FORM-QC-008", "Document FORM-QC-008 has been submitted for your review and approval.", "/documents/"),
            (users["tariq_qc"], "Calibration Due Soon: Digital Caliper 150mm", "Equipment EQ-CAL-002 is due for calibration within 20 days.", "/calibration/"),
        ]
        for rec, title, msg, link in notifs:
            Notification.objects.get_or_create(
                recipient=rec,
                title=title,
                defaults={'message': msg, 'link': link}
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded comprehensive industrial QMS Hub demo data!"))
