from django import forms
from .models import Special
from django.core.exceptions import ValidationError

class SpecialForm(forms.ModelForm):
    CTA_CHOICES = [
        ("order", "Click to Order"),
        ("call", "Call Now"),
        ("mobile_order", "Mobile Order"),
    ]

    # Change this to match your model field name
    cta_choices = forms.ChoiceField(
        choices=CTA_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Choose One Call to Action"
    )

    class Meta:
        model = Special
        fields = [
            "title", "description", "image", "start_date", "end_date",
            "cta_choices", "order_url", "phone_number", "mobile_order_url", "enable_email_signup"
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Detect partial update by checking if only a few fields are present
        # csrf + 1 field = 2 keys; csrf + multiple = 3–5
        is_partial = len(self.data) <= 5  # allow a few fields

        if is_partial:
            return cleaned_data  # ✅ skip full-form validation

        # 🔥 Full validation only for full form submissions
        cta = cleaned_data.get("cta_choices")  # Changed from cta_choice to cta_choices

        if not cta:
            raise ValidationError("Please select a call-to-action.")

        if cta == "order" and not cleaned_data.get("order_url"):
            self.add_error("order_url", "Order URL is required if Click to Order is selected.")
        elif cta == "call" and not cleaned_data.get("phone_number"):
            self.add_error("phone_number", "Phone Number is required if Call Now is selected.")
        elif cta == "mobile_order" and not cleaned_data.get("mobile_order_url"):
            self.add_error("mobile_order_url", "Mobile Order URL is required if Mobile Order is selected.")

        return cleaned_data


class SpecialDescriptionForm(forms.ModelForm):
    class Meta:
        model = Special
        fields = ["description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }