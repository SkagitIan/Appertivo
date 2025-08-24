from django import forms
from .models import Special


class SpecialForm(forms.ModelForm):
    class Meta:
        model = Special
        fields = [
            "title",
            "description",
            "price",
            "image",
            "start_date",
            "end_date",
            "cta_type",
            "cta_url",
            "cta_phone",
        ]
