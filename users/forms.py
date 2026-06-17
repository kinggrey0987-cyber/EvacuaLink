from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Form for creating new users with role assignment"""

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    phone_number = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3}
        ),
    )
    role = forms.ChoiceField(
        choices=[(User.Role.ADMIN, "Administrator"), (User.Role.STAFF, "Staff")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number", "address", "role", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

        # Add help text
        self.fields['username'].help_text = 'Required. 4 to 20 characters. Letters, digits and @/./+/-/_ only.'
        self.fields['phone_number'].help_text = 'Optional. Contact phone number'
        self.fields['address'].help_text = 'Optional. Physical address'

    def clean_email(self):
        """Validate that email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def clean_username(self):
        """Validate that username is unique and valid length"""
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 4 or len(username) > 20:
                raise ValidationError("Username must be between 4 and 20 characters long.")
            if User.objects.filter(username=username).exists():
                raise ValidationError("This username is already taken.")
        return username


class CustomUserChangeForm(UserChangeForm):
    """Form for updating user information"""

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    phone_number = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3}
        ),
    )
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number", "address", "role")

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        # Hide password field in change form
        if 'password' in self.fields:
            del self.fields['password']

        # Add Bootstrap classes
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].help_text = 'Required. 4 to 20 characters. Letters, digits and @/./+/-/_ only.'
        
        # Security: Only Tech Admins can change roles
        if current_user and not current_user.is_technical_admin:
            if 'role' in self.fields:
                self.fields['role'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        queryset = User.objects.filter(email=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if email and queryset.exists():
            raise ValidationError("This email address is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 4 or len(username) > 20:
                raise ValidationError("Username must be between 4 and 20 characters long.")
            queryset = User.objects.filter(username=username)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("This username is already taken.")
        return username


class UserLoginForm(forms.Form):
    """Form for user login"""

    username = forms.CharField(
        label="Username or Email",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Enter your username or email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Enter your password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Remember me",
    )
