from django.urls import path
from . import views

urlpatterns = [
    # --- Public ---
    path('', views.skill_list, name='skill-list'),
    path('skill/<int:pk>/', views.skill_detail, name='skill-detail'),

    # --- Auth ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Skill CRUD ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('skill/new/', views.skill_create, name='skill-create'),
    path('skill/<int:pk>/edit/', views.skill_update, name='skill-update'),
    path('skill/<int:pk>/delete/', views.skill_delete, name='skill-delete'),

    # --- Reviews ---
    path('skill/<int:pk>/review/', views.add_review, name='add-review'),
    path('review/<int:pk>/delete/', views.delete_review, name='delete-review'),

    # --- Bookings ---
    path('skill/<int:pk>/book/', views.book_skill, name='book-skill'),
    path('booking/<int:pk>/<str:status>/', views.update_booking_status, name='update-booking'),

    # --- Profile ---
    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change-password'),
    path('profile/delete/', views.delete_account, name='delete-account'),

    # --- Public user profiles + user ratings ---
    path('user/<str:username>/', views.public_profile, name='public-profile'),
    path('user/<str:username>/rate/', views.rate_user, name='rate-user'),
    path('user-rating/<int:pk>/delete/', views.delete_user_rating, name='delete-user-rating'),
]
