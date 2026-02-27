from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "blog"

urlpatterns = [

    # =====================
    # HOME / BLOG
    # =====================
    path("", views.blog_home, name="home"),

    # =====================
    # ADMIN BLOG POSTS (BlogPost)
    # =====================
    path("like/<slug:slug>/", views.ajax_toggle_like, name="toggle_like"),
    path("comment/add/<slug:slug>/", views.ajax_add_comment, name="comment_add"),
    path("comment/delete/<int:comment_id>/", views.ajax_delete_comment, name="comment_delete"),
    path("comment/edit/<int:comment_id>/", views.ajax_edit_comment, name="comment_edit"),

    # =====================
    # STATIC PAGES
    # =====================
    path("about/", views.blog_about, name="about"),
    path("contact/", views.blog_contact, name="contact"),
    path("case-studies/", views.blog_case_studies, name="case_studies"),

    # =====================
    # USER POSTS (UserPost)
    # =====================
    path("user-post/<int:post_id>/", views.user_post_detail, name="user_post_detail"),

    # 🔹 USER POST LIKE
    path(
        "user-post/<int:post_id>/like/",
        views.ajax_toggle_userpost_like,
        name="userpost_like",
    ),

    # 🔹 USER POST COMMENT ADD
    path(
        "user-post/<int:post_id>/comment/add/",
        views.ajax_add_userpost_comment,
        name="userpost_comment_add",
    ),

    # 🔹 USER POST COMMENT DELETE
    path(
        "user-post/comment/<int:comment_id>/delete/",
        views.ajax_delete_userpost_comment,
        name="userpost_comment_delete",
    ),

    # =====================
    # PROFILE / DASHBOARD
    # =====================
    path("profile/", views.blog_profile, name="profile"),
    path("profile/post/<int:post_id>/edit/", views.edit_user_post, name="edit_user_post"),
    path("profile/post/<int:post_id>/delete/", views.delete_user_post, name="delete_user_post"),
    path("my-comments/", views.blog_my_comments, name="my_comments"),

    # =====================
    # AUTH
    # =====================
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="blog/login.html",
            redirect_authenticated_user=True,
            extra_context={"next": "/blog/profile/"},
        ),
        name="login",
    ),
    path("signup/", views.blog_signup, name="signup"),
    path("logout/", views.blog_logout, name="logout"),

    # =====================
    # PUBLIC PROFILE
    # =====================
    path("u/<str:username>/", views.public_profile, name="public_profile"),

    # =====================
    # BLOG DETAIL (KEEP LAST)
    # =====================
    path("<slug:slug>/", views.blog_detail, name="detail"),
]
