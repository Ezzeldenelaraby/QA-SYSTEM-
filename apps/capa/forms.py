from django import forms
from .models import CAPA

class CAPAForm(forms.ModelForm):
    class Meta:
        model = CAPA
        fields = [
            'title', 'source', 'related_ncr', 'related_finding', 'related_risk',
            'description', 'root_cause', 'corrective_action', 'preventive_action',
            'responsible_person', 'start_date', 'due_date', 'verification_method',
            'status', 'evidence', 'evidence_file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Clear CAPA project title'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'related_ncr': forms.Select(attrs={'class': 'form-select'}),
            'related_finding': forms.Select(attrs={'class': 'form-select'}),
            'related_risk': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'root_cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'corrective_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'preventive_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'verification_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Statistical Cpk review, audit check...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'evidence_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CAPAEffectivenessForm(forms.ModelForm):
    class Meta:
        model = CAPA
        fields = ['effectiveness_result']
        widgets = {
            'effectiveness_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide objective evidence, data metrics, and dates verifying non-recurrence...'}),
        }
