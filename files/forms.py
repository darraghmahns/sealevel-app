# files/forms.py

from django import forms
from .models import File
from django.contrib.auth import get_user_model

User = get_user_model()

class FileUploadForm(forms.ModelForm):
    owner_email = forms.EmailField(
        required=False,
        label='Patient Email',
        help_text='Enter the email of the patient if you are a provider.'
    )

    class Meta:
        model = File
        fields = ['file', 'description', 'owner_email']

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with the user instance to adjust fields based on user role.
        """
        self.user = kwargs.pop('user', None)
        super(FileUploadForm, self).__init__(*args, **kwargs)
        
        if self.user and self.user.is_provider:
            # If the user is a provider, make 'owner_email' required
            self.fields['owner_email'].required = True
        else:
            # If the user is a patient, hide the 'owner_email' field
            self.fields['owner_email'].widget = forms.HiddenInput()

    def clean_owner_email(self):
        """
        Validate the 'owner_email' field if it's visible.
        """
        owner_email = self.cleaned_data.get('owner_email')
        
        if self.user and self.user.is_provider:
            if not owner_email:
                raise forms.ValidationError("Please provide the patient's email.")
            try:
                owner = User.objects.get(email=owner_email)
                return owner
            except User.DoesNotExist:
                raise forms.ValidationError("No patient found with this email.")
        return self.user  # If user is a patient, return themselves

    def save(self, commit=True):
        """
        Save the File instance, setting 'owner' and 'uploaded_by' based on user role.
        """
        file_instance = super(FileUploadForm, self).save(commit=False)
        
        if self.user and self.user.is_provider:
            file_instance.owner = self.cleaned_data.get('owner_email')
            file_instance.uploaded_by = self.user
        else:
            file_instance.owner = self.user
            file_instance.uploaded_by = self.user
        
        if commit:
            file_instance.save()
        return file_instance