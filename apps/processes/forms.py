from django import forms
from .models import Process

class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = [
            'code', 'name', 'department', 'process_owner', 'description',
            'inputs', 'outputs', 'equipment', 'tools', 'parameters',
            'inspection_points', 'quality_gates', 'status'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PRC-CNC-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CNC 5-Axis Precision Machining'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'process_owner': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Raw materials, drawings, specs...'}),
            'outputs': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Finished parts, inspection records...'}),
            'equipment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Major machine tools, fixtures...'}),
            'tools': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Cutting tools, dies, fixtures...'}),
            'parameters': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Speed, feed, temp, pressure...'}),
            'inspection_points': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'First article, in-process, final...'}),
            'quality_gates': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Mandatory release criteria...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
