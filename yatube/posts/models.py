from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Название сообщества')
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name='Описание сообщества')

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(blank=False, verbose_name='Текст поста',
                            help_text='Напишите текст записи')
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор')
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True, null=True, related_name='posts',
                              verbose_name='Сообщество',
                              help_text='Укажите сообщество')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, verbose_name='Пост',
                             related_name='comments',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User, verbose_name='Автор',
                               related_name='comments',
                               on_delete=models.CASCADE)
    text = models.TextField(blank=False, null=True,
                            verbose_name='Комментарий')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата комментария')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-created',)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, 'Подписчик', related_name='follower')
    author = models.ForeignKey(User, 'Инфлюенсер', related_name='following')

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_following'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')), name='no_self_following'
            )
        )
