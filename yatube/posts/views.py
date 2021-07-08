from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from yatube.settings import POST_COUNT


def paginator(request, post_list):
    paginator = Paginator(post_list, POST_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return page


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page = paginator(request, post_list)
    return render(request, 'posts/index.html',
                  {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page = paginator(request, post_list)
    return render(request, 'posts/group.html',
                  {'group': group,
                   'page': page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_count = author.posts.count()
    follower_count = author.follower.count()
    following_count = author.following.count()
    page = paginator(request, post_list)
    is_following = Follow.objects.filter(user=request.user,
                                         author=author).exists()
    return render(request, 'posts/profile.html',
                  {'author': author,
                   'page': page,
                   'posts_count': posts_count,
                   'follower_count': follower_count,
                   'following_count': following_count,
                   'is_following': is_following})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    posts_count = post.author.posts.count()
    follower_count = post.author.follower.count()
    following_count = post.author.following.count()
    is_following = Follow.objects.filter(user=request.user,
                                         author=post.author).exists()
    return render(request, 'posts/post.html',
                  {'post': post,
                   'comments': comments,
                   'form': form,
                   'is_following': is_following,
                   'posts_count': posts_count,
                   'follower_count': follower_count,
                   'following_count': following_count})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'posts/new_post.html',
                  {'form': form, 'to_edit': False})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('post_view', post_id=post_id,
                        username=post.author)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post_view', post_id=post_id,
                        username=request.user.username)
    return render(request, 'posts/new_post.html',
                  {'form': form, 'to_edit': True, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    form = CommentForm(
        request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post_view', post_id=post_id,
                        username=request.user.username)
    return render(request, 'posts/comments.html',
                  {'form': form, 'post': post, 'comments': comments})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page = paginator(request, post_list)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
