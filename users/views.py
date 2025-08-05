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
    from files.models import File, FileAccess
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    user = request.user
    
    # Calculate user statistics
    if user.is_provider:
        # Provider stats - files they uploaded for patients
        total_files = File.objects.filter(uploaded_by=user).count()
        files_this_month = File.objects.filter(
            uploaded_by=user,
            uploaded_date__gte=datetime.now().replace(day=1)
        ).count()
        patients_served = File.objects.filter(uploaded_by=user).values('owner').distinct().count()
        recent_activity = f"Uploaded {files_this_month} files this month for {patients_served} patients"
    else:
        # Patient stats - their own files
        total_files = File.objects.filter(owner=user).count()
        files_this_month = File.objects.filter(
            owner=user,
            uploaded_date__gte=datetime.now().replace(day=1)
        ).count()
        shared_files = FileAccess.objects.filter(user=user).count()
        files_shared_by_me = FileAccess.objects.filter(file__owner=user).count()
        recent_activity = f"Added {files_this_month} files this month"
    
    # Recent files
    if user.is_provider:
        recent_files = File.objects.filter(uploaded_by=user).order_by('-uploaded_date')[:3]
    else:
        recent_files = File.objects.filter(owner=user).order_by('-uploaded_date')[:3]
    
    context = {
        "name": user.first_name or user.email.split('@')[0],
        "user": user,
        "total_files": total_files,
        "files_this_month": files_this_month,
        "recent_activity": recent_activity,
        "recent_files": recent_files,
    }
    
    # Add role-specific stats
    if user.is_provider:
        context["patients_served"] = patients_served
        context["role"] = "Healthcare Provider"
    else:
        context["shared_files"] = shared_files
        context["files_shared_by_me"] = files_shared_by_me
        context["role"] = "Patient"
    
    return render(request, 'users/home.html', context)

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