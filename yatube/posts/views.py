from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings

from posts.models import Post, Group, Follow
from posts.forms import PostForm, CommentForm


def paginator(page_number, posts):
    paginator = Paginator(posts, settings.POSTS_ON_PAGE)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group')
    page_number = request.GET.get('page')
    page_obj = paginator(page_number, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_number = request.GET.get('page')
    page_obj = paginator(page_number, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_number = request.GET.get('page')
    page_obj = paginator(page_number, posts)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        id=post_id,
    )
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.all(),
        'post_id': post_id,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None,)
    context = {
        'form': form,
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        pk=post_id,
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    context = {
        'form': form,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        pk=post_id,
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    page_obj = paginator(page_number, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.filter(user=user, author__username=username).delete()
    return redirect('posts:profile', username=username)
