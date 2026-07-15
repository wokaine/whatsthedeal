from django import forms
from .models import Post, Supermarket

class PostCreateForm(forms.Form):
    supermarket = forms.ModelChoiceField(
        queryset=Supermarket.objects.all(),
        empty_label=None
    )
    main = forms.CharField(max_length=100, required=True)
    side = forms.CharField(max_length=100, required=True)
    side_2 = forms.CharField(max_length=100, required=False)
    drink = forms.CharField(max_length=100, required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)
    image = forms.ImageField(required=False)

class PostEditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["description", "image"]

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, required=True)
