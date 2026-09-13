from django import forms
from .models import ManagementReviewMeeting

class ManagementReviewMeetingForm(forms.ModelForm):
    class Meta:
        model = ManagementReviewMeeting
        fields = [
            'title', 'meeting_date', 'chairperson', 'participants', 'status',
            'general_summary',
            'inputs_previous_actions', 'inputs_audit_results', 'inputs_customer_feedback',
            'inputs_process_performance', 'inputs_quality_objectives', 'inputs_ncr_capa_status',
            'inputs_supplier_performance', 'inputs_risks_opportunities', 'inputs_resource_needs',
            'inputs_improvement_opportunities',
            'outputs_decisions', 'outputs_resource_requirements', 'outputs_improvement_projects'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Annual Quality Management Review 2026'}),
            'meeting_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'chairperson': forms.Select(attrs={'class': 'form-select'}),
            'participants': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List names and functional titles of attendees'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'general_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Executive summary, opening remarks and overall evaluation'}),
            
            # Inputs
            'inputs_previous_actions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_audit_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_customer_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_process_performance': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_quality_objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_ncr_capa_status': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_supplier_performance': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_risks_opportunities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_resource_needs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'inputs_improvement_opportunities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # Outputs
            'outputs_decisions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'outputs_resource_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'outputs_improvement_projects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
