from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User  ,UserPreference , review,Trip, PhotoInteraction# Use custom User model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm 
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import random  # For captcha generation
import string
from django.contrib.auth import authenticate

User = get_user_model()

def generate_captcha(length=6):
    """Generate a random captcha with letters, numbers, and special characters."""
    characters = string.ascii_letters + string.digits + "_%&"
    return ''.join(random.choices(characters, k=length))


#   Custom UserCreationForm
class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(max_length=150, required=True) 
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    nationality = forms.CharField(max_length=50)
    city = forms.CharField(max_length=50)
    postal_address = forms.CharField(max_length=255)
    mobile_number = forms.CharField(max_length=15)
    preferred_travel_season = forms.ChoiceField(choices=[('summer', 'Summer'), ('winter', 'Winter'), ('spring', 'Spring'), ('autumn', 'Autumn')])
    preferred_travel_type = forms.ChoiceField(choices=[('adventure', 'Adventure'), ('hiking', 'Hiking'), ('beach', 'Beach'), ('cultural', 'Cultural'), ('luxury', 'Luxury')])
    age_range = forms.ChoiceField(choices=[('18-25', '18-25'), ('26-35', '26-35'), ('36-50', '36-50'), ('51+', '51+')])
    budget_range = forms.ChoiceField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    captcha = forms.CharField(
        max_length=10, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "Enter Captcha", "autocomplete": "off"})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  #   Extract request safely
        super().__init__(*args, **kwargs)

        #   Store captcha in session if request exists
        if self.request and "captcha_value" not in self.request.session:
            self.request.session["captcha_value"] = generate_captcha()
        self.fields['captcha'].help_text = f"Enter: {self.request.session.get('captcha_value', 'XXXX')}"  # Prevents errors

    def clean_captcha(self):
        input_value = self.cleaned_data.get('captcha')

        #   Ensure request exists before accessing session
        if self.request:
            correct_value = self.request.session.get("captcha_value", None)
            if input_value != correct_value:
                raise ValidationError("Incorrect captcha. Please try again.")

        return input_value
    
    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'nationality', 'city', 'postal_address', 'mobile_number', 'email', 'password1', 'password2', 'preferred_travel_season', 'preferred_travel_type', 'age_range', 'budget_range']


#   Custom Login Form
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Mobile Number")  #   Use correct label
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        mobile_number = self.cleaned_data.get("username")  #   Get mobile number
        password = self.cleaned_data.get("password")

        #   Find the user by `mobile_number`
        try:
            user = User.objects.get(mobile_number=mobile_number)
        except User.DoesNotExist:
            raise ValidationError("Invalid mobile number or password.")

        #   Authenticate using `username`
        user = authenticate(username=user.username, password=password)

        if not user:
            raise ValidationError("Invalid mobile number or password.")

        self.cleaned_data["user"] = user  #   Store user in form data
        return self.cleaned_data

class UserProfileForm(forms.ModelForm):
    # Include User fields
    first_name = forms.CharField(max_length=50, required=True, label="First Name")
    last_name = forms.CharField(max_length=50, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email")
    city = forms.CharField(max_length=100, required=False, label="City")

    class Meta:
        model = UserPreference  # Primary model for preferences
        fields = ['season', 'activity_type', 'budget']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get user object from view
        super().__init__(*args, **kwargs)

        # Pre-fill user data
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['city'].initial = user.city

class FeedbackForm(forms.ModelForm):
    class Meta:
        model =  review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        
        
class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['title', 'start_date', 'end_date' ,'accommodation', 'activities', 'is_shared']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'accommodation': forms.Textarea(attrs={'rows': 2}),
            'activities': forms.Textarea(attrs={'rows': 2}),
         
        }

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = PhotoInteraction
        fields = ['image', 'caption']