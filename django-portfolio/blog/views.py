from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import BlogSignupForm, BlogCommentForm, UserPostForm

from django.contrib.auth import logout, login

from django.contrib.auth import get_backends
import markdown
from django.contrib.auth.models import User
from .models import (
    BlogPost, Comment, Like, UserPost,
    UserPostLike, UserPostComment
)
from django.db.models import Count, Sum, F
from django.db.models.functions import Coalesce




def blog_home(request):
    admin_posts = (
        BlogPost.objects
        .select_related("category", "author")
        .filter(status="published")
        .order_by("-created_at")
    )

    user_posts = (
        UserPost.objects
        .select_related("category", "user")
        .order_by("-created_at")
    )

    # 🔥 Attach reading time dynamically
    

    return render(request, "blog/home.html", {
        "admin_posts": admin_posts,
        "user_posts": user_posts,
    })


def blog_category(request, slug):
    category = get_object_or_404(Category, slug=slug)

    posts = (
        BlogPost.objects
        .select_related('category', 'author')
        .prefetch_related('likes', 'shares')
        .filter(category=category, status='published')
        .order_by('-created_at')
    )

    context = {
        'category': category,
        'posts': posts,
    }

    return render(request, 'blog/category.html', context)





def blog_detail(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related("category", "author"),
        slug=slug,
        status="published"
    )

    comments = post.comments.filter(is_approved=True)
    comment_form = BlogCommentForm()

    for c in comments:
        c.rendered_content = markdown.markdown(
            c.content,
            extensions=["fenced_code", "tables"]
        )

    # 👇 reading time

    return render(request, "blog/detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
       
    })


def blog_about(request):
    return render(request, 'blog/about.html')

def blog_contact(request):
    return render(request, 'blog/contact.html')

def blog_case_studies(request):
    return render(request, 'blog/case_studies.html')


@login_required
def blog_profile(request):
    user = request.user

    user_posts = (
        UserPost.objects
        .filter(user=user)
        .annotate(
            total_likes=Count("likes", distinct=True),
            total_comments=Count("comments", distinct=True),
        )
    )

    totals = {
        "total_views": user_posts.aggregate(v=Coalesce(Sum("views"), 0))["v"],
        "total_likes": UserPostLike.objects.filter(post__user=user).count(),
        "total_comments": UserPostComment.objects.filter(post__user=user).count(),
    }

    # CREATE POST
    if request.method == "POST":
        post_form = UserPostForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.user = user
            post.save()
            return redirect("blog:profile")
    else:
        post_form = UserPostForm()

    return render(request, "blog/profile.html", {
        "post_form": post_form,
        "user_posts": user_posts,
        "total_views": totals["total_views"],
        "total_likes": totals["total_likes"],
        "total_comments": totals["total_comments"],
    })


@login_required
@require_POST
def delete_user_post(request, post_id):
    post = get_object_or_404(UserPost, id=post_id, user=request.user)
    post.delete()
    return redirect("blog:profile")



@login_required
def edit_user_post(request, post_id):
    post = get_object_or_404(UserPost, id=post_id, user=request.user)

    if request.method == "POST":
        form = UserPostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            post = form.save(commit=False)

            # 🔴 REMOVE IMAGE → stay on edit page
            if "remove_image" in request.POST:
                if post.image:
                    post.image.delete(save=False)
                post.image = None
                post.save()
                return redirect("blog:edit_user_post", post_id=post.id)

            # 🔴 REMOVE VIDEO → stay on edit page
            if "remove_video" in request.POST:
                if post.video:
                    post.video.delete(save=False)
                post.video = None
                post.save()
                return redirect("blog:edit_user_post", post_id=post.id)

            # ✅ SAVE CHANGES → go to profile
            if "save" in request.POST:
                post.save()
                return redirect("blog:profile")

    else:
        form = UserPostForm(instance=post)

    return render(
        request,
        "blog/edit_post.html",
        {
            "form": form,
            "post": post,
        },
    )




@login_required
def blog_my_comments(request):
    return render(request, 'blog/my_comments.html')

def blog_logout(request):
    logout(request)
    return redirect('blog:home')




def blog_signup(request):
    if request.method == "POST":
        form = BlogSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()

            # ✅ Fix for multiple authentication backends
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)

            return redirect("blog:profile")
    else:
        form = BlogSignupForm()

    return render(request, "blog/signup.html", {"form": form})



@login_required
@require_POST
def ajax_add_comment(request, slug):
    post = BlogPost.objects.get(slug=slug)
    content = request.POST.get("content", "").strip()

    if not content:
        return JsonResponse({"error": "Empty comment"}, status=400)

    comment = Comment.objects.create(
        post=post,
        user=request.user,
        content=content
    )

    return JsonResponse({
        "id": comment.id,
        "user": comment.user.username,
        "created": comment.created_at.strftime("%b %d, %Y"),
        "content": markdown.markdown(comment.content),
        "is_owner": True,   # 👈 IMPORTANT
    })



@login_required
@require_POST
def ajax_delete_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id, user=request.user)
    comment.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def ajax_edit_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id, user=request.user)
    content = request.POST.get("content", "").strip()

    if not content:
        return JsonResponse({"error": "Empty content"}, status=400)

    comment.content = content
    comment.save()

    return JsonResponse({
        "content": markdown.markdown(comment.content)
    })


@login_required
@require_POST
def ajax_toggle_like(request, slug):
    post = BlogPost.objects.get(slug=slug)
    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user
    )

    if not created:
        like.delete()

    return JsonResponse({
        "liked": created,
        "count": post.likes.count()
    })

@login_required
def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    user_posts = (
        UserPost.objects
        .filter(user=profile_user)
        .annotate(
            total_likes=Count("likes", distinct=True),
            total_comments=Count("comments", distinct=True),
        )
    )

    totals = {
        "total_views": user_posts.aggregate(
            v=Coalesce(Sum("views"), 0)
        )["v"],

        "total_likes": UserPostLike.objects.filter(
            post__user=profile_user
        ).count(),

        "total_comments": UserPostComment.objects.filter(
            post__user=profile_user
        ).count(),
    }

    return render(request, "blog/public_profile.html", {
        "profile_user": profile_user,
        "user_posts": user_posts,
        "total_views": totals["total_views"],
        "total_likes": totals["total_likes"],
        "total_comments": totals["total_comments"],
    })


def user_post_detail(request, post_id):
    post = get_object_or_404(
        UserPost.objects.select_related("category", "user"),
        id=post_id
    )

    # 👁️ count views (once per session)
    session_key = f"userpost_viewed_{post.id}"
    if not request.session.get(session_key):
        UserPost.objects.filter(id=post.id).update(views=F("views") + 1)
        request.session[session_key] = True
        post.refresh_from_db()

    comments = post.comments.select_related("user")

    # 👇 reading time

    return render(request, "blog/user_post_detail.html", {
        "post": post,
        "comments": comments,
       
    })

@login_required
@require_POST
def ajax_toggle_userpost_like(request, post_id):
    post = get_object_or_404(UserPost, id=post_id)

    like, created = UserPostLike.objects.get_or_create(
        post=post,
        user=request.user
    )

    if not created:
        like.delete()

    return JsonResponse({
        "liked": created,
        "count": post.likes.count()
    })

@login_required
@require_POST
def ajax_add_userpost_comment(request, post_id):
    post = get_object_or_404(UserPost, id=post_id)
    content = request.POST.get("content", "").strip()

    if not content:
        return JsonResponse({"error": "Empty comment"}, status=400)

    comment = UserPostComment.objects.create(
        post=post,
        user=request.user,
        content=content
    )

    return JsonResponse({
        "id": comment.id,
        "user": comment.user.username,
        "created": comment.created_at.strftime("%b %d, %Y"),
        "content": comment.content,
        "is_owner": True,
    })

@login_required
@require_POST
def ajax_delete_userpost_comment(request, comment_id):
    comment = get_object_or_404(
        UserPostComment,
        id=comment_id,
        user=request.user
    )
    comment.delete()
    return JsonResponse({"success": True})
