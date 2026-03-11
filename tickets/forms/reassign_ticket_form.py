from django import forms
from tickets.models import User


class ReassignTicketForm(forms.Form):

    reassign = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type=User.USER_TYPE_STAFF),
        required=False,
        label="Forward to staff",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
