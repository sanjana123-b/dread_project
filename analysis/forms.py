from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Project, Threat, UserProfile


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Online Banking Portal'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                   'placeholder': 'Brief description of the system/application'}),
        }


RATING_WIDGET = forms.Select(attrs={'class': 'form-select rating-select'})


class ThreatForm(forms.ModelForm):
    class Meta:
        model = Threat
        fields = [
            'title', 'description', 'stride_category',
            'damage', 'reproducibility', 'exploitability', 'affected_users', 'discoverability',
            'mitigation', 'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SQL Injection on login form'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stride_category': forms.Select(attrs={'class': 'form-select'}),
            'damage': RATING_WIDGET,
            'reproducibility': RATING_WIDGET,
            'exploitability': RATING_WIDGET,
            'affected_users': RATING_WIDGET,
            'discoverability': RATING_WIDGET,
            'mitigation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                  'placeholder': 'How should this be mitigated?'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
