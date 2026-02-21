from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Listing, Profile, ForumPost, ForumReply


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
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['listing'].queryset = Listing.objects.filter(seller=user, is_sold=False)
            self.fields['listing'].required = False
            self.fields['listing'].label = 'Link your listing (optional)'
            self.fields['listing'].empty_label = 'None - just a discussion'


class ForumReplyForm(forms.ModelForm):
    class Meta:
        model = ForumReply
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a reply...'}),
        }
