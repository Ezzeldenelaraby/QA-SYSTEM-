from django import forms
from .models import Action

class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = [
            'title', 'description', 'source_type', 'source_id',
            'department', 'process', 'assigned_to', 'priority',
            'start_date', 'due_date', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Clear, actionable title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'source_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. NCR-2026-0001'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class ActionCompleteForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['evidence', 'evidence_file']
        widgets = {
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Document implementation results and attach verification evidence...'}),
            'evidence_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ActionVerifyForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['verification']
        widgets = {
            'verification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Supervisor/QA verification comments confirming effectiveness...'}),
        }
