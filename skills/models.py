from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


class UserProfile(models.Model):
    """Extends the built-in User with a custom public-facing ID chosen by the user."""

    # OneToOneField: every User gets exactly one UserProfile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # The ID the user picks themselves — unique so no two people share the same one
    custom_id = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True,
        help_text='Pick a unique public ID, e.g. BU2024_OD or CSE42. Letters, numbers, underscores only.'
    )

    def __str__(self):
        return f"{self.user.username} — {self.custom_id or 'no custom ID'}"

    def display_id(self):
        """Returns the custom ID if set, otherwise falls back to the database pk."""
        return self.custom_id if self.custom_id else f'#{self.user.pk}'


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('tech', 'Technology'),
        ('music', 'Music'),
        ('art', 'Art & Design'),
        ('language', 'Language'),
        ('tutoring', 'Tutoring'),
        ('fitness', 'Fitness'),
        ('cooking', 'Cooking'),
        ('other', 'Other'),
    ]

    CONTACT_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('instagram', 'Instagram'),
        ('in_app', 'In-App Message'),
    ]

    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy — Limited Slots'),
        ('unavailable', 'Unavailable'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_free = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text='Leave blank if free'
    )
    contact_preference = models.CharField(max_length=20, choices=CONTACT_CHOICES, default='email')
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.owner.username}"

    def get_absolute_url(self):
        return reverse('skill-detail', kwargs={'pk': self.pk})

    def average_rating(self):
        """Returns the average star rating across all reviews, or None if no reviews."""
        reviews = self.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def review_count(self):
        return self.reviews.count()


class Review(models.Model):
    """A star rating + comment left by one user on another user's skill post."""

    STAR_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1 through 5

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='reviews')
    # reviewer: the person who wrote the review (not the skill owner)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.PositiveSmallIntegerField(
        choices=STAR_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # One review per user per skill — prevents duplicate reviews
        unique_together = ('skill', 'reviewer')

    def __str__(self):
        return f"{self.reviewer.username} → {self.skill.title} ({self.rating}★)"


class UserRating(models.Model):
    """A star rating one user gives directly to another user (not tied to a skill)."""

    STAR_CHOICES = [(i, str(i)) for i in range(1, 6)]

    # rater: the person giving the rating
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    # rated_user: the person being rated
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    rating = models.PositiveSmallIntegerField(
        choices=STAR_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, help_text='Optional: say why you rated them this way')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # One rating per pair — a user can only rate another user once
        unique_together = ('rater', 'rated_user')

    def __str__(self):
        return f"{self.rater.username} → {self.rated_user.username} ({self.rating}★)"

    @staticmethod
    def average_for(user):
        """Returns the average star rating for a given user, or None."""
        qs = UserRating.objects.filter(rated_user=user)
        if not qs.exists():
            return None
        return round(qs.aggregate(avg=Avg('rating'))['avg'], 1)

    @staticmethod
    def count_for(user):
        return UserRating.objects.filter(rated_user=user).count()


class BookingRequest(models.Model):
    """A session request sent from one user to a skill owner."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='bookings')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    message = models.TextField(help_text='Briefly describe what you need help with.')
    # Optional: requester proposes a date
    proposed_date = models.DateField(null=True, blank=True, help_text='Optional: suggest a date')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.requester.username} → {self.skill.title} [{self.status}]"
