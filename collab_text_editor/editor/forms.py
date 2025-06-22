from django import forms
from django.contrib.auth.models import User
from .models import CollaboratorRole, Document


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class AddCollaboratorForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Select User")
    role = forms.ChoiceField(choices=CollaboratorRole.ROLE_CHOICES, label="Access Level")

    class Meta:
        model = CollaboratorRole
        fields = ['user', 'role']


class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'content']


