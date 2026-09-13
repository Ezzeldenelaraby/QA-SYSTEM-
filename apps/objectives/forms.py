from django import forms
from .models import QualityObjective, ObjectiveMeasurement

class QualityObjectiveForm(forms.ModelForm):
    class Meta:
        model = QualityObjective
        fields = [
            'code', 'name', 'department', 'process', 'description',
            'kpi', 'measurement_method', 'baseline', 'target', 'actual_result',
            'unit', 'start_date', 'due_date', 'responsible_person', 'status', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. OBJ-2026-01'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CNC Scrap Reduction'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'kpi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Scrap Rate (%)'}),
            'measurement_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Scrap parts / total parts'}),
            'baseline': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_result': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '%, PPM, Days'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ObjectiveMeasurementForm(forms.ModelForm):
    class Meta:
        model = ObjectiveMeasurement
        fields = ['period_date', 'value', 'notes']
        widgets = {
            'period_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional context or explanation'}),
        }
