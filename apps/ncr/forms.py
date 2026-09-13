from django import forms
from .models import NCR, FiveWhysAnalysis, FishboneCause

class NCRForm(forms.ModelForm):
    class Meta:
        model = NCR
        fields = [
            'date', 'department', 'process', 'product', 'batch_lot',
            'reported_by', 'source', 'description', 'requirement',
            'evidence', 'evidence_file', 'classification', 'severity',
            'immediate_correction', 'containment_action', 'root_cause_summary',
            'responsible_person', 'due_date', 'status'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Part Name or Assembly'}),
            'batch_lot': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. LOT-2026-0901'}),
            'reported_by': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed nonconformity observation...'}),
            'requirement': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Drawing specification, ISO clause, or tolerance...'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Measurement logs, photos, inspection notes...'}),
            'evidence_file': forms.FileInput(attrs={'class': 'form-control'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'immediate_correction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Immediate quarantine, sorting, or rework...'}),
            'containment_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Actions taken to stop escapes to customer...'}),
            'root_cause_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Summary of confirmed root cause...'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class FiveWhysForm(forms.ModelForm):
    class Meta:
        model = FiveWhysAnalysis
        fields = ['problem_statement', 'why_1', 'why_2', 'why_3', 'why_4', 'why_5', 'root_cause_conclusion']
        widgets = {
            'problem_statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'State the exact problem clearly'}),
            'why_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1. Why did it happen?'}),
            'why_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2. Why?'}),
            'why_3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3. Why?'}),
            'why_4': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '4. Why?'}),
            'why_5': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '5. Why? (Fundamental Root Cause)'}),
            'root_cause_conclusion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Root cause conclusion'}),
        }

class FishboneCauseForm(forms.ModelForm):
    class Meta:
        model = FishboneCause
        fields = ['category', 'cause_description', 'is_primary']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'cause_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific contributing cause'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class NCRCloseForm(forms.ModelForm):
    class Meta:
        model = NCR
        fields = ['immediate_correction', 'containment_action', 'root_cause_summary', 'verification_notes']
        widgets = {
            'immediate_correction': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'containment_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'root_cause_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'verification_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'QA verification findings and formal sign-off statement'}),
        }
