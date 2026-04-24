"""
All email notification functions for Campus SkillSwap.

Keeping emails in one file makes them easy to find, edit, and test.
Each function accepts the relevant model objects and calls send_mail().

During development (EMAIL_BACKEND = console), emails print to the terminal.
Switch to the SMTP backend in settings.py to send real emails.
"""
from django.core.mail import send_mail
from django.conf import settings


def notify_owner_new_booking(booking):
    """
    Email sent to the skill owner when someone requests a session.

    booking: a BookingRequest instance (already saved to the database)
    """
    owner = booking.skill.owner
    requester = booking.requester

    if not owner.email:
        return   # skip silently if the owner has no email on file

    subject = f'New booking request for "{booking.skill.title}"'

    proposed = (
        booking.proposed_date.strftime('%B %d, %Y')
        if booking.proposed_date else 'No date proposed'
    )

    body = f"""Hi {owner.username},

{requester.username} has requested a session for your skill:

  Skill     : {booking.skill.title}
  Message   : {booking.message}
  Proposed  : {proposed}

Log in to your dashboard to accept or decline the request:
  http://127.0.0.1:8000/dashboard/

— Campus SkillSwap
"""

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[owner.email],
        fail_silently=True,   # don't crash the page if email fails
    )


def notify_requester_status_update(booking):
    """
    Email sent to the requester when the owner accepts or declines their booking.

    booking: a BookingRequest instance (status already updated)
    """
    requester = booking.requester
    owner = booking.skill.owner

    if not requester.email:
        return

    status_word = 'accepted' if booking.status == 'accepted' else 'declined'

    subject = f'Your booking request was {status_word} — {booking.skill.title}'

    if booking.status == 'accepted':
        next_step = (
            f'Great news! {owner.username} has accepted your request. '
            f'Reach out to them via {booking.skill.get_contact_preference_display()} to confirm the details.'
        )
    else:
        next_step = (
            f'Unfortunately {owner.username} is unable to take this session right now. '
            f'Browse other skills at http://127.0.0.1:8000/'
        )

    body = f"""Hi {requester.username},

Your session request for "{booking.skill.title}" has been {status_word}.

{next_step}

View your bookings: http://127.0.0.1:8000/dashboard/

— Campus SkillSwap
"""

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[requester.email],
        fail_silently=True,
    )
