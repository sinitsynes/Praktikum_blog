from django import forms
from django.forms import widgets

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'image', 'group')
        labels = {
            'text': 'Текст записи',
            'group': 'Сообщество',
            'image': 'Иллюстрация'
        }
        help_texts = {
            'text': 'Напишите текст записи',
            'group': 'Укажите сообщество',
            'image': 'Добавьте картинку'
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': widgets.Textarea}
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Оставьте комментарий'}
