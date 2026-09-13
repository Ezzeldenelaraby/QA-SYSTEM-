from django import forms
from .models import AuditPlan, AuditChecklistItem, AuditFinding

class AuditPlanForm(forms.ModelForm):
    class Meta:
        model = AuditPlan
        fields = [
            'audit_title', 'department', 'process', 'lead_auditor', 'audit_team',
            'audit_date', 'scope', 'criteria', 'status', 'summary_notes'
        ]
        widgets = {
            'audit_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ISO 9001 Clause 8.5 Operations Audit'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'lead_auditor': forms.Select(attrs={'class': 'form-select'}),
            'audit_team': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 3}),
            'audit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Audited manufacturing lines, shifts, and boundaries...'}),
            'criteria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ISO 9001:2015 Clauses 7, 8, Quality Manual'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'summary_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AuditChecklistForm(forms.ModelForm):
    class Meta:
        model = AuditChecklistItem
        fields = ['iso_clause', 'question', 'requirement', 'evidence', 'result', 'comment']
        widgets = {
            'iso_clause': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 7.1.5'}),
            'question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Audit check question'}),
            'requirement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Standard requirement'}),
            'evidence': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sampled records, observations'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auditor remarks'}),
        }

class AuditFindingForm(forms.ModelForm):
    class Meta:
        model = AuditFinding
        fields = ['finding_type', 'description', 'clause', 'evidence', 'responsible_person', 'due_date', 'status']
        widgets = {
            'finding_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'clause': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 8.5.1'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
