from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import PDFFile, Message, ChatRoom

# Form for user sign-up
class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# Form for login
class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

# Form for uploading P


class PDFFileForm(forms.ModelForm):
    day_published = forms.CharField(
        max_length=2,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Day (e.g., 05)'})
    )
    month_published = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Month (e.g., January)'})
    )

    class Meta:
        model = PDFFile
        fields = ['file', 'subject', 'name', 'description', 'year_published', 'day_published', 'month_published']

class MessageForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'message-input',
            'placeholder': 'Type your message...',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Message
        fields = ['content']

# Form for creating group chats
class GroupChatForm(forms.ModelForm):
    name = forms.CharField(max_length=255, required=True, help_text="Enter the group name")
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = ChatRoom
        fields = ['name', 'participants']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['participants'].queryset = User.objects.exclude(id=user.id)
