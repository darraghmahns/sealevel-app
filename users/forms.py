from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('provider', 'Provider'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Use email as username
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        # Set the role
        role = self.cleaned_data.get('role')
        if role == 'provider':
            user.is_provider = True
        else:
            user.is_provider = False
            
        if commit:
            user.save()
        return user