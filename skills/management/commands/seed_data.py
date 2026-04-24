"""
Management command: py manage.py seed_data

Creates realistic dummy users, skill posts, reviews, and booking requests
so the dashboard shows a full, populated experience.
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from skills.models import Skill, Review, BookingRequest


USERS = [
    ('ada_codes',    'ada@campus.edu',      'Pass1234!'),
    ('marcus_fit',   'marcus@campus.edu',   'Pass1234!'),
    ('zoe_art',      'zoe@campus.edu',      'Pass1234!'),
    ('liam_music',   'liam@campus.edu',     'Pass1234!'),
    ('priya_lang',   'priya@campus.edu',    'Pass1234!'),
    ('carlos_cook',  'carlos@campus.edu',   'Pass1234!'),
]

SKILLS_DATA = [
    {
        'owner': 'ada_codes',
        'title': 'Python for Beginners',
        'description': 'I will teach you Python from scratch — variables, loops, functions, and building a simple project. Perfect if you have never coded before.',
        'category': 'tech',
        'is_free': False, 'price': 15.00,
        'contact_preference': 'whatsapp',
        'availability': 'available',
    },
    {
        'owner': 'ada_codes',
        'title': 'Web Development with Django',
        'description': 'Learn to build full-stack web apps with Django. Covers models, views, templates, forms, and deployment basics.',
        'category': 'tech',
        'is_free': False, 'price': 20.00,
        'contact_preference': 'email',
        'availability': 'busy',
    },
    {
        'owner': 'marcus_fit',
        'title': 'Campus Fitness Coaching',
        'description': 'Personalised workout plan and 1-on-1 coaching sessions. I specialise in strength training and HIIT for busy students.',
        'category': 'fitness',
        'is_free': False, 'price': 10.00,
        'contact_preference': 'instagram',
        'availability': 'available',
    },
    {
        'owner': 'marcus_fit',
        'title': 'Nutrition & Meal Planning',
        'description': 'Student-budget friendly meal planning to keep you energised during exams. Includes a personalised weekly plan.',
        'category': 'fitness',
        'is_free': True, 'price': None,
        'contact_preference': 'whatsapp',
        'availability': 'available',
    },
    {
        'owner': 'zoe_art',
        'title': 'Graphic Design with Canva',
        'description': 'Create stunning posters, social media graphics, and presentations using Canva. Great for students running clubs or events.',
        'category': 'art',
        'is_free': False, 'price': 12.00,
        'contact_preference': 'instagram',
        'availability': 'available',
    },
    {
        'owner': 'zoe_art',
        'title': 'Sketchbook & Illustration Basics',
        'description': 'Relax and learn to draw! I teach basic line art, shading, and composition in a fun, pressure-free session.',
        'category': 'art',
        'is_free': True, 'price': None,
        'contact_preference': 'in_app',
        'availability': 'available',
    },
    {
        'owner': 'liam_music',
        'title': 'Guitar Lessons for Beginners',
        'description': 'Learn your first chords, strumming patterns, and 3 complete songs within a month. Acoustic or electric.',
        'category': 'music',
        'is_free': False, 'price': 18.00,
        'contact_preference': 'whatsapp',
        'availability': 'available',
    },
    {
        'owner': 'priya_lang',
        'title': 'Conversational Spanish',
        'description': 'Hablo español fluently! Practice everyday conversations, grammar basics, and build confidence speaking Spanish.',
        'category': 'language',
        'is_free': False, 'price': 8.00,
        'contact_preference': 'email',
        'availability': 'available',
    },
    {
        'owner': 'priya_lang',
        'title': 'Hindi for Absolute Beginners',
        'description': 'Learn Hindi script, basic greetings, numbers, and common phrases. Perfect for beginners starting from zero.',
        'category': 'language',
        'is_free': True, 'price': None,
        'contact_preference': 'whatsapp',
        'availability': 'available',
    },
    {
        'owner': 'carlos_cook',
        'title': 'Quick Student Meals (Under 30 min)',
        'description': 'I will teach you 10 tasty, cheap meals you can make in your dorm. No fancy equipment needed.',
        'category': 'cooking',
        'is_free': False, 'price': 5.00,
        'contact_preference': 'instagram',
        'availability': 'available',
    },
    {
        'owner': 'carlos_cook',
        'title': 'Baking Basics — Bread & Pastries',
        'description': 'Learn to bake sourdough, banana bread, and simple pastries from scratch. We will do a live session together.',
        'category': 'cooking',
        'is_free': False, 'price': 10.00,
        'contact_preference': 'email',
        'availability': 'busy',
    },
]

REVIEW_TEMPLATES = [
    (5, 'Absolutely brilliant session! Learned so much in just one hour. Highly recommend.'),
    (5, 'Super patient and explains everything clearly. Worth every penny!'),
    (4, 'Really helpful and knowledgeable. The session ran a little over time but in a good way.'),
    (4, 'Great experience. Would definitely book again for a follow-up session.'),
    (3, 'Good session overall. Some parts moved a bit fast but they answered all my questions.'),
    (5, 'Best tutor on campus. I went from knowing nothing to building my first project!'),
    (4, 'Very friendly and accommodating. Materials were well prepared.'),
    (5, 'I loved every minute. Already recommended to three of my friends!'),
    (3, 'Decent session. Could use more hands-on practice but theory was solid.'),
    (5, 'Exceeded my expectations. Came in confused, left feeling confident!'),
]

BOOKING_MESSAGES = [
    'Hi! I\'d love to learn more about this. Can we schedule a session this week?',
    'I\'ve been looking for help with exactly this topic. Would Thursday work?',
    'Super interested! I\'m a complete beginner — is that okay?',
    'Can we do an online session instead of in-person? Happy to be flexible.',
    'I saw your profile and this is exactly what I need before my exam next week.',
    'Would you be open to a 2-hour session? I\'m happy to pay more.',
    'This looks amazing. I\'m free most evenings — what works for you?',
]


class Command(BaseCommand):
    help = 'Seeds the database with dummy users, skills, reviews, and bookings'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # Create dummy users
        user_objects = {}
        for username, email, password in USERS:
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'  Created user: {username}')
            user_objects[username] = user

        # Create skill posts
        skill_objects = []
        for data in SKILLS_DATA:
            owner = user_objects[data.pop('owner')]
            skill, created = Skill.objects.get_or_create(
                title=data['title'],
                owner=owner,
                defaults={**data}
            )
            if created:
                self.stdout.write(f'  Created skill: {skill.title}')
            skill_objects.append(skill)

        # Create reviews — each user reviews skills they don't own
        for skill in skill_objects:
            reviewers = [u for u in user_objects.values() if u != skill.owner]
            # Give each skill 2–4 reviews
            for reviewer in random.sample(reviewers, k=min(random.randint(2, 4), len(reviewers))):
                if not Review.objects.filter(skill=skill, reviewer=reviewer).exists():
                    rating, comment = random.choice(REVIEW_TEMPLATES)
                    Review.objects.create(skill=skill, reviewer=reviewer, rating=rating, comment=comment)

        self.stdout.write(f'  Created reviews')

        # Create booking requests
        for skill in skill_objects:
            requesters = [u for u in user_objects.values() if u != skill.owner]
            for requester in random.sample(requesters, k=min(2, len(requesters))):
                if not BookingRequest.objects.filter(skill=skill, requester=requester).exists():
                    days_ahead = random.randint(1, 14)
                    BookingRequest.objects.create(
                        skill=skill,
                        requester=requester,
                        message=random.choice(BOOKING_MESSAGES),
                        proposed_date=date.today() + timedelta(days=days_ahead),
                        status=random.choice(['pending', 'pending', 'accepted', 'declined']),
                    )

        self.stdout.write(f'  Created bookings')
        self.stdout.write(self.style.SUCCESS('\nDone! Database seeded successfully.'))
        self.stdout.write('Dummy user password for all accounts: Pass1234!')
