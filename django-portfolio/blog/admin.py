
from django.contrib import admin
from .models import BlogPost, Category, Comment, Like, Share, UserPost

admin.site.register(UserPost)



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    autocomplete_fields = ('category', 'author')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'author', 'status')
        }),
        ('Content', {
            'fields': ('excerpt', 'content')
        }),
        ('SEO (Optional)', {
            'classes': ('collapse',),
            'fields': ('seo_title', 'seo_description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'user__username', 'post__title')
    actions = ['approve_comments', 'disapprove_comments']
    readonly_fields = ('created_at',)

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"

    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_comments.short_description = "Disapprove selected comments"

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('created_at',)


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('post', 'platform', 'created_at')
    list_filter = ('platform', 'created_at')
    search_fields = ('post__title',)
    readonly_fields = ('created_at',)
