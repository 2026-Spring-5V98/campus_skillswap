from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg

from django.contrib.auth.models import User
from .models import Skill, Review, BookingRequest, UserRating, UserProfile
from .forms import SkillForm, RegisterForm, ReviewForm, BookingForm, ProfileForm, UserRatingForm, UserProfileForm, CustomPasswordChangeForm
from .emails import notify_owner_new_booking, notify_requester_status_update


# ---------------------------------------------------------------------------
# Public views
# ---------------------------------------------------------------------------

def skill_list(request):
    """Homepage with keyword search and category filter."""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')

    skills = Skill.objects.all()

    if query:
        skills = skills.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        skills = skills.filter(category=category)

    return render(request, 'skills/skill_list.html', {
        'skills': skills,
        'query': query,
        'selected_category': category,
        'categories': Skill.CATEGORY_CHOICES,
    })


def skill_detail(request, pk):
    """Full view of one skill post, with its reviews, booking button, and owner rating form."""
    skill = get_object_or_404(Skill, pk=pk)
    reviews = skill.reviews.select_related('reviewer')

    user_review = None
    already_booked = False
    user_rating_form = None
    existing_user_rating = None

    if request.user.is_authenticated and request.user != skill.owner:
        user_review = Review.objects.filter(skill=skill, reviewer=request.user).first()
        already_booked = BookingRequest.objects.filter(
            skill=skill, requester=request.user
        ).exists()
        existing_user_rating = UserRating.objects.filter(
            rater=request.user, rated_user=skill.owner
        ).first()
        if not existing_user_rating:
            user_rating_form = UserRatingForm()

    return render(request, 'skills/skill_detail.html', {
        'skill': skill,
        'reviews': reviews,
        'user_review': user_review,
        'already_booked': already_booked,
        'user_rating_form': user_rating_form,
        'existing_user_rating': existing_user_rating,
    })


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def register_view(request):
    if request.user.is_authenticated:
        return redirect('skill-list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Campus SkillSwap, {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'skills/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('skill-list')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Incorrect username or password.')
    return render(request, 'skills/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('skill-list')


# ---------------------------------------------------------------------------
# Skill CRUD views
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Personal dashboard: the user's skills, incoming bookings, and reviews received."""
    my_skills = Skill.objects.filter(owner=request.user).prefetch_related('reviews', 'bookings')

    # Incoming booking requests on the user's skills
    incoming_bookings = BookingRequest.objects.filter(
        skill__owner=request.user
    ).select_related('requester', 'skill').order_by('-requested_at')

    # Bookings the user made for other people's skills
    my_bookings = BookingRequest.objects.filter(
        requester=request.user
    ).select_related('skill', 'skill__owner').order_by('-requested_at')

    # Skill review stats
    total_reviews = Review.objects.filter(skill__owner=request.user).count()
    avg_rating = Review.objects.filter(
        skill__owner=request.user
    ).aggregate(avg=Avg('rating'))['avg']

    # User-to-user rating stats (from UserRating model)
    user_ratings_received = UserRating.objects.filter(
        rated_user=request.user
    ).select_related('rater').order_by('-created_at')
    user_avg_rating = UserRating.average_for(request.user)
    user_rating_count = UserRating.count_for(request.user)

    return render(request, 'skills/dashboard.html', {
        'my_skills': my_skills,
        'incoming_bookings': incoming_bookings,
        'my_bookings': my_bookings,
        'total_reviews': total_reviews,
        'user_ratings_received': user_ratings_received,
        'user_avg_rating': user_avg_rating,
        'user_rating_count': user_rating_count,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
    })


@login_required
def skill_create(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.owner = request.user
            skill.save()
            messages.success(request, 'Skill posted successfully!')
            return redirect('skill-detail', pk=skill.pk)
    else:
        form = SkillForm()
    return render(request, 'skills/skill_form.html', {'form': form, 'action': 'Post'})


@login_required
def skill_update(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if skill.owner != request.user:
        messages.error(request, 'You can only edit your own skill posts.')
        return redirect('skill-detail', pk=pk)
    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill updated.')
            return redirect('skill-detail', pk=skill.pk)
    else:
        form = SkillForm(instance=skill)
    return render(request, 'skills/skill_form.html', {'form': form, 'action': 'Update'})


@login_required
def skill_delete(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if skill.owner != request.user:
        messages.error(request, 'You can only delete your own skill posts.')
        return redirect('skill-detail', pk=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill post deleted.')
        return redirect('dashboard')
    return render(request, 'skills/skill_confirm_delete.html', {'skill': skill})


# ---------------------------------------------------------------------------
# Review views
# ---------------------------------------------------------------------------

@login_required
def add_review(request, pk):
    """Submit a star rating and comment for a skill."""
    skill = get_object_or_404(Skill, pk=pk)

    # Owner should not review their own skill
    if skill.owner == request.user:
        messages.error(request, "You can't review your own skill.")
        return redirect('skill-detail', pk=pk)

    # Prevent duplicate reviews
    if Review.objects.filter(skill=skill, reviewer=request.user).exists():
        messages.warning(request, 'You have already reviewed this skill.')
        return redirect('skill-detail', pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.skill = skill
            review.reviewer = request.user
            review.save()
            messages.success(request, 'Review submitted!')
            return redirect('skill-detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'skills/review_form.html', {'form': form, 'skill': skill})


@login_required
def delete_review(request, pk):
    """Let a reviewer delete their own review."""
    review = get_object_or_404(Review, pk=pk, reviewer=request.user)
    skill_pk = review.skill.pk
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect('skill-detail', pk=skill_pk)


# ---------------------------------------------------------------------------
# Booking views
# ---------------------------------------------------------------------------

@login_required
def book_skill(request, pk):
    """Submit a booking request for a skill."""
    skill = get_object_or_404(Skill, pk=pk)

    if skill.owner == request.user:
        messages.error(request, "You can't book your own skill.")
        return redirect('skill-detail', pk=pk)

    if BookingRequest.objects.filter(skill=skill, requester=request.user).exists():
        messages.warning(request, 'You already have a pending request for this skill.')
        return redirect('skill-detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.skill = skill
            booking.requester = request.user
            booking.save()
            notify_owner_new_booking(booking)   # email the skill owner
            messages.success(request, f'Booking request sent to {skill.owner.username}!')
            return redirect('skill-detail', pk=pk)
    else:
        form = BookingForm()

    return render(request, 'skills/booking_form.html', {'form': form, 'skill': skill})


@login_required
def update_booking_status(request, pk, status):
    """Skill owner accepts or declines a booking request."""
    booking = get_object_or_404(BookingRequest, pk=pk, skill__owner=request.user)

    if status in ('accepted', 'declined'):
        booking.status = status
        booking.save()
        notify_requester_status_update(booking)  # email the requester
        messages.success(request, f'Booking {status}.')

    return redirect('dashboard')


# ---------------------------------------------------------------------------
# Profile view
# ---------------------------------------------------------------------------

@login_required
def profile(request):
    """Lets the logged-in user update their name, email, and custom public ID."""
    # get_or_create ensures every user has a UserProfile row, even older accounts
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

    return render(request, 'skills/profile.html', {
        'form': form,
        'profile_form': profile_form,
    })


# ---------------------------------------------------------------------------
# Public user profile + user-to-user rating
# ---------------------------------------------------------------------------

def public_profile(request, username):
    """Shows any user's public profile: their skills, ratings received, and a form to rate them."""
    profile_user = get_object_or_404(User, username=username)
    skills = Skill.objects.filter(owner=profile_user)
    ratings = UserRating.objects.filter(rated_user=profile_user).select_related('rater')

    avg_rating = UserRating.average_for(profile_user)
    rating_count = UserRating.count_for(profile_user)

    # Has the logged-in user already rated this person?
    existing_rating = None
    rating_form = None
    if request.user.is_authenticated and request.user != profile_user:
        existing_rating = UserRating.objects.filter(
            rater=request.user, rated_user=profile_user
        ).first()
        if not existing_rating:
            rating_form = UserRatingForm()

    return render(request, 'skills/public_profile.html', {
        'profile_user': profile_user,
        'skills': skills,
        'ratings': ratings,
        'avg_rating': avg_rating,
        'rating_count': rating_count,
        'existing_rating': existing_rating,
        'rating_form': rating_form,
    })


@login_required
def rate_user(request, username):
    """Handles the POST when a user submits a star rating for another user."""
    rated_user = get_object_or_404(User, username=username)
    # 'next' lets the form redirect back to wherever the rating form was shown
    next_url = request.POST.get('next') or request.GET.get('next') or 'public-profile'

    def go_back():
        if next_url.startswith('/'):
            return redirect(next_url)
        return redirect('public-profile', username=username)

    if rated_user == request.user:
        messages.error(request, "You can't rate yourself.")
        return go_back()

    if UserRating.objects.filter(rater=request.user, rated_user=rated_user).exists():
        messages.warning(request, 'You have already rated this user.')
        return go_back()

    if request.method == 'POST':
        form = UserRatingForm(request.POST)
        if form.is_valid():
            user_rating = form.save(commit=False)
            user_rating.rater = request.user
            user_rating.rated_user = rated_user
            user_rating.save()
            messages.success(request, f'You rated {rated_user.username} {user_rating.rating}★!')
            return go_back()

    return go_back()


@login_required
def delete_user_rating(request, pk):
    """Lets a rater delete their own user rating."""
    user_rating = get_object_or_404(UserRating, pk=pk, rater=request.user)
    username = user_rating.rated_user.username
    user_rating.delete()
    messages.success(request, 'Rating removed.')
    return redirect('public-profile', username=username)


# ---------------------------------------------------------------------------
# Password change + account deletion
# ---------------------------------------------------------------------------

@login_required
def change_password(request):
    """Lets a logged-in user change their password."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keeps the user logged in
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'skills/change_password.html', {'form': form})


@login_required
def delete_account(request):
    """Lets a logged-in user permanently delete their own account."""
    if request.method == 'POST':
        confirm = request.POST.get('confirm_username', '').strip()
        if confirm == request.user.username:
            request.user.delete()
            logout(request)
            messages.success(request, 'Your account has been deleted.')
            return redirect('skill-list')
        else:
            messages.error(request, 'Username did not match. Account was not deleted.')
            return redirect('delete-account')
    return render(request, 'skills/delete_account.html')
