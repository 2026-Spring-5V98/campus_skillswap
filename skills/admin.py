from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Skill, Review, BookingRequest, UserRating, UserProfile


# Unregister the default User admin, then re-register with our custom version
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Columns shown in the user list
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined')
    # Make the name columns sortable and searchable
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'is_free', 'price', 'availability', 'created_at')
    list_filter = ('category', 'availability', 'is_free')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'skill', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('reviewer__username', 'skill__title')
    readonly_fields = ('created_at',)


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'skill', 'status', 'proposed_date', 'requested_at')
    list_filter = ('status',)
    search_fields = ('requester__username', 'skill__title')
    readonly_fields = ('requested_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'custom_id')
    search_fields = ('user__username', 'custom_id')


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'rated_user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('rater__username', 'rated_user__username')
    readonly_fields = ('created_at',)
