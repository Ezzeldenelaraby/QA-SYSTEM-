from django import forms
from .models import Equipment

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'equipment_id', 'equipment_name', 'category', 'manufacturer',
            'model', 'serial_number', 'department', 'location', 'measurement_range',
            'accuracy', 'calibration_frequency_months', 'last_calibration_date',
            'calibration_provider', 'certificate_file', 'status', 'notes'
        ]
        widgets = {
            'equipment_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EQ-CAL-001'}),
            'equipment_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mitutoyo Digimatic Micrometer'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mitutoyo, Zeiss'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lab Bench 2, Line A'}),
            'measurement_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0 - 25 mm'}),
            'accuracy': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+/- 0.001 mm'}),
            'calibration_frequency_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'last_calibration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'calibration_provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Internal Metrology Lab'}),
            'certificate_file': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
