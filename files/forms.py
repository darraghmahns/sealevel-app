# files/forms.py

from django import forms
from .models import File
from users.models import User

class FileUploadForm(forms.ModelForm):
    owner_email = forms.EmailField(
        required=False,
        label='Patient Email',
        help_text='Enter the email of the patient if you are a provider.'
    )

    class Meta:
        model = File
        fields = ['uploaded_file', 'owner_email']  # Include 'owner_email' in the fields

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract 'user' from kwargs
        super(FileUploadForm, self).__init__(*args, **kwargs)

        if user and user.is_provider:
            # If the user is a provider, make 'owner_email' required
            self.fields['owner_email'].required = True
            self.fields['owner_email'].widget.attrs.update({
                'placeholder': 'Patient Email',
                'class': 'form-control',
            })
        else:
            # If the user is not a provider, remove the 'owner_email' field
            self.fields.pop('owner_email')