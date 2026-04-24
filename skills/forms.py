from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Skill, Review, BookingRequest, UserRating, UserProfile


def add_bootstrap_classes(form):
    """Inject Bootstrap CSS classes into every field widget on a form."""
    for field_name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs['class'] = 'form-check-input'
        elif isinstance(widget, forms.Select):
            widget.attrs['class'] = 'form-select'
        else:
            widget.attrs['class'] = 'form-control'


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['title', 'description', 'category', 'is_free', 'price',
                  'contact_preference', 'availability']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('is_free') and not cleaned_data.get('price'):
            raise forms.ValidationError('Please enter a price, or tick the "Free" checkbox.')
        return cleaned_data


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)


class ReviewForm(forms.ModelForm):
    """Star rating + comment for a skill."""

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your experience…'}),
            # Radio buttons for star rating feel more natural than a dropdown
            'rating': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].required = False
        self.fields['rating'].label = 'Your Rating'
        # Apply form-control only to comment; RadioSelect doesn't need it
        self.fields['comment'].widget.attrs['class'] = 'form-control'


class ProfileForm(forms.ModelForm):
    """Lets a logged-in user update their first name, last name, and email."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        add_bootstrap_classes(self)


class UserProfileForm(forms.ModelForm):
    """Lets a user set their custom public-facing ID."""

    class Meta:
        model = UserProfile
        fields = ['custom_id']
        widgets = {
            'custom_id': forms.TextInput(attrs={'placeholder': 'e.g. BU2024_OD'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)

    def clean_custom_id(self):
        value = self.cleaned_data.get('custom_id', '').strip()
        if not value:
            return None   # allow blank (falls back to pk display)
        import re
        if not re.match(r'^[\w]+$', value):
            raise forms.ValidationError('Only letters, numbers, and underscores allowed.')
        return value


class UserRatingForm(forms.ModelForm):
    """Star rating + optional comment for rating another user directly."""

    class Meta:
        model = UserRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(),
            'comment': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Optional — tell them why you gave this rating…'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].required = False
        self.fields['rating'].label = 'Your Rating'
        self.fields['comment'].widget.attrs['class'] = 'form-control'


class CustomPasswordChangeForm(PasswordChangeForm):
    """Password change form styled with Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)


class BookingForm(forms.ModelForm):
    """Request form a student fills in to book a skill session."""

    class Meta:
        model = BookingRequest
        fields = ['message', 'proposed_date']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
            'proposed_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
