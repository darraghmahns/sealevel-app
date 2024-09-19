# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"  # Correct template path

@login_required
def home(request):
    context = {"name": request.user.first_name}
    return render(request, '../templates/users/home.html', context)  # Correct template path

def landing(request):
    return render(request, '../templates/users/landing.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home page after login
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    else:
        return render(request, 'registration/login.html')