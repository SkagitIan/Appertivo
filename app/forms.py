# forms.py
from django import forms
from django.core.exceptions import ValidationError
from cloudinary import uploader
from cloudinary.utils import cloudinary_url
from .models import Special

class SpecialForm(forms.ModelForm):
    CTA_CHOICES = [
        ("order", "Click to Order"),
        ("call", "Call Now"),
        ("mobile_order", "Mobile Order"),
    ]

    # non-model field used only to accept uploads
    image_file = forms.ImageField(required=False)

    cta_choices = forms.ChoiceField(
        choices=CTA_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Choose One Call to Action",
    )

    class Meta:
        model = Special
        fields = [
            "title", "description", "price",
            # NOTE: do NOT include 'image' here; it's a URLField on the model
            "start_date", "end_date", "image",
            "cta_choices", "order_url", "phone_number",
            "mobile_order_url", "enable_email_signup",
        ]
        widgets = {
            # make sure dates are HTML date inputs (see Issue 2 below)
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
            "end_date":   forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),

            "price":      forms.TextInput(attrs={"class": "form-control", "inputmode": "decimal"}),
            # use plain FileInput so Django doesn't render the "Currently/Clear" UI
            "image":      forms.FileInput(attrs={"class": "form-control d-none", "accept": "image/png,image/jpeg"}),
        }

    def save(self, commit=True):
        """Upload image_file to Cloudinary and store resulting URL in model.image."""
        instance = super().save(commit=False)

        # If you're storing a single CTA, consider normalizing to a list here:
        if isinstance(self.cleaned_data.get("cta_choices"), str):
            instance.cta_choices = [self.cleaned_data["cta_choices"]]

        image_file = self.cleaned_data.get("image_file")
        if image_file:
            try:
                upload_result = uploader.upload(image_file, folder="specials")
                optimized_url, _ = cloudinary_url(
                    upload_result["public_id"],
                    format="jpg", quality="auto", secure=True,
                )
                instance.image = optimized_url  # URLField on the model
            except Exception as e:
                raise ValidationError(f"Cloudinary upload failed: {e}")

        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned = super().clean()

        # Skip full validation for partial HTMX updates
        if len(self.data) <= 5:
            return cleaned

        cta = cleaned.get("cta_choices")
        if not cta:
            raise ValidationError("Please select a call-to-action.")

        if cta == "order" and not cleaned.get("order_url"):
            self.add_error("order_url", "Order URL is required if Click to Order is selected.")
        elif cta == "call" and not cleaned.get("phone_number"):
            self.add_error("phone_number", "Phone Number is required if Call Now is selected.")
        elif cta == "mobile_order" and not cleaned.get("mobile_order_url"):
            self.add_error("mobile_order_url", "Mobile Order URL is required if Mobile Order is selected.")

        return cleaned
