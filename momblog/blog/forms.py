from django import forms
from .models import Post, Category

class PostForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
