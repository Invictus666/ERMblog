from django import forms
from .models import Post, Comment, Vote
from django.core.exceptions import ValidationError
from django.core import validators

class CommentForm(forms.Form):
    comment = forms.CharField(required=True, max_length=500, min_length=3, strip=True)

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'ticker', 'current_price', 'target_price',
            'current_yield', 'projected_yield', 'business',
            'pros', 'cons', 'include', 'rationale',
        ]
        widgets = {
            'business':  forms.Textarea(attrs={'rows': 6}),
            'pros':      forms.Textarea(attrs={'rows': 6}),
            'cons':      forms.Textarea(attrs={'rows': 6}),
            'rationale': forms.Textarea(attrs={'rows': 4}),
        }
