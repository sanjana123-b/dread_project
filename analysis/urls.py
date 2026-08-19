from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='root_redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('projects/', views.project_list, name='project_list'),
    path('projects/new/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:project_pk>/export/', views.export_csv, name='export_csv'),

    path('projects/<int:project_pk>/threats/new/', views.threat_create, name='threat_create'),
    path('threats/<int:pk>/', views.threat_detail, name='threat_detail'),
    path('threats/<int:pk>/edit/', views.threat_edit, name='threat_edit'),
    path('threats/<int:pk>/delete/', views.threat_delete, name='threat_delete'),
]
