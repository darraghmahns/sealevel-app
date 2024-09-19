from django.urls import path
from .views import SignUp, home, landing
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', landing, name='landing'),
    path('signup/', SignUp.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
]