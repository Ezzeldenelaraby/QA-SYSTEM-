from django import forms
from .models import Risk

class RiskForm(forms.ModelForm):
    class Meta:
        model = Risk
        fields = [
            'process', 'department', 'description', 'cause',
            'potential_consequence', 'existing_control', 'likelihood',
            'severity', 'action_required', 'responsible_person',
            'due_date', 'status', 'effectiveness', 'evidence', 'review_date'
        ]
        widgets = {
            'process': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describe the risk failure mode...'}),
            'cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Root causes or vulnerabilities...'}),
            'potential_consequence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Impact on safety, quality, or delivery...'}),
            'existing_control': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Existing preventive/detective controls...'}),
            'likelihood': forms.Select(attrs={'class': 'form-select', 'id': 'id_likelihood'}),
            'severity': forms.Select(attrs={'class': 'form-select', 'id': 'id_severity'}),
            'action_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'effectiveness': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
