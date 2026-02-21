from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Listing, Profile, ForumPost, ForumReply, Transaction


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'category', 'condition',
            'image', 'school', 'contact_info'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'school', 'phone', 'contact_info', 'address', 'bio', 'avatar']
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'e.g. Sampaloc, Manila or near LRT Legarda'}),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }


class MessageForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}))


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ['title', 'body', 'listing']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your listing, ask questions, or chat with the community...'}),
            'listing': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['listing'].queryset = Listing.objects.filter(seller=user, is_sold=False)
            self.fields['listing'].required = False
            self.fields['listing'].label = 'Link your listing (optional)'
            self.fields['listing'].empty_label = 'None - just a discussion'
    
    def __str__(self):
        return "Forum Post"


class ForumReplyForm(forms.ModelForm):
    class Meta:
        model = ForumReply
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a reply...'}),
        }

class PurchaseForm(forms.ModelForm):
    """Form for initiating a purchase with exchange method and notes."""
    class Meta:
        model = Transaction
        fields = ['exchange_method', 'notes']
        widgets = {
            'exchange_method': forms.RadioSelect(choices=Transaction.EXCHANGE_METHOD_CHOICES),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add any notes for the seller (e.g., "Can meet at SM Mall" or "Available after 5pm")',
                'class': 'form-control'
            }),
        }
        labels = {
            'exchange_method': 'How would you like to exchange payment & goods?',
            'notes': 'Message to seller (optional)',
        }


class TransactionConfirmForm(forms.ModelForm):
    """Form for seller to confirm transaction with their notes."""
    class Meta:
        model = Transaction
        fields = ['seller_notes']
        widgets = {
            'seller_notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Confirm availability, location, or other details (e.g., "Available Sat-Sun 2-5pm" or "My number: 09xxxxxxxxx")',
                'class': 'form-control'
            }),
        }
        labels = {
            'seller_notes': 'Your confirmation & meeting details (optional)',
        }