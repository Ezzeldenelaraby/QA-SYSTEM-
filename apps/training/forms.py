from django import forms
from .models import Course, TrainingRecord

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'course_type', 'related_process', 'related_document', 'validity_months', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TRN-SOP-01'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5-Axis CNC Setup & Operation'}),
            'course_type': forms.Select(attrs={'class': 'form-select'}),
            'related_process': forms.Select(attrs={'class': 'form-select'}),
            'related_document': forms.Select(attrs={'class': 'form-select'}),
            'validity_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ['employee', 'course', 'trainer', 'training_date', 'expiry_date', 'result', 'competency_status', 'certificate_file', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'trainer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Trainer Name / Institution'}),
            'training_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'competency_status': forms.Select(attrs={'class': 'form-select'}),
            'certificate_file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
