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

class ImageClearableFileInput(forms.ClearableFileInput):
    initial_text = 'Current Image'
    input_text = 'Change Image'
    clear_checkbox_label = 'Remove Image'
    template_name = 'widgets/image_clearable_file_input.html'

class PostEditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["description", "image"]
        widgets = {
            'image': ImageClearableFileInput
        }

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, required=True)
