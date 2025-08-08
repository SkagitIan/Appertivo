from django import forms
from specialwidget.models import Special
from django.forms import ModelForm, Textarea, ModelChoiceField,TextInput,Select,CheckboxInput
from django.contrib.auth.forms import AuthenticationForm, UsernameField, UserCreationForm
from cloudinary.forms import CloudinaryFileField
import cloudinary 
from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper


cloudinary.config(
    cloud_name = 'dfz4bhlzs',
    api_key = '258173152359737',
    api_secret = 'rNOhGbPWTjdXof0aKs656ThFLNc')

class AddSpecialForm(ModelForm):
    class Meta:
        model = Special
        fields = ['title','description','image','price','expires','membership']
        widget = forms.TextInput(attrs={'class':'form-control'})
        widgets = {'title':forms.TextInput(attrs={'placeholder':'Special'}),
                'description':forms.Textarea(attrs={'placeholder':"Description",'rows':5}),
                'price':forms.TextInput(attrs={'placeholder':"Price"}),
                }
        labels = {'title':"Special",
                    'description':"Description",
                    'image':"Upload Picture",
                    'price':"Special Price"}
        placeholder = {'title':"Special",
                            'expires':'Expires'
                        }

    def __init__(self, *args, **kwargs):
        
        super(AddSpecialForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False 



class SignUpForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]
        user = User(username=email, email=email)
        user.set_password(password)
        if commit:
            user.save()
        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = UsernameField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))
    remember_me = forms.BooleanField(required=False, initial=False, label="Remember me")
