from django import forms
from .models import Inspection, InspectionItem

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = [
            'date', 'process', 'product', 'batch_lot', 'machine',
            'inspector', 'shift', 'overall_result', 'comments'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Part Name or Assembly'}),
            'batch_lot': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. LOT-2026-0915'}),
            'machine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hermle C42U Mill #1'}),
            'inspector': forms.Select(attrs={'class': 'form-select'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'overall_result': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class InspectionItemForm(forms.ModelForm):
    class Meta:
        model = InspectionItem
        fields = ['checkpoint_name', 'specification', 'measured_value', 'unit', 'result', 'comment', 'photo']
        widgets = {
            'checkpoint_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bore Diameter'}),
            'specification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50.00 +/- 0.02 mm'}),
            'measured_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Actual measurement'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'mm, Ra, Bar'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observations'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
