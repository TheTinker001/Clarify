from django import forms
from tickets.models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['faculty', 'study_level', 'category', 'subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }