from django import forms
from .models import Document, DocumentRevision

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'document_number', 'title', 'document_type', 'department', 'process',
            'revision_number', 'issue_date', 'effective_date', 'review_date',
            'owner', 'prepared_by', 'reviewed_by', 'file_attachment',
            'revision_reason', 'notes'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SOP-QA-001'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. In-Process Quality Inspection Procedure'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'revision_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'prepared_by': forms.Select(attrs={'class': 'form-select'}),
            'reviewed_by': forms.Select(attrs={'class': 'form-select'}),
            'file_attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'revision_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class NewRevisionForm(forms.Form):
    new_revision_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 02, B, etc.'}))
    revision_reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe modifications and rationale for new revision...'}), required=True)
    new_file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)
