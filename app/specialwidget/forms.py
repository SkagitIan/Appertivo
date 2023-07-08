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


