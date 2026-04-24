from django import template
from skills.models import UserProfile

register = template.Library()


@register.filter
def public_id(user):
    """Returns the user's chosen custom ID, or their pk as a fallback.
    Usage in templates:  {{ some_user|public_id }}
    """
    try:
        cid = user.profile.custom_id
        return cid if cid else f'#{user.pk}'
    except UserProfile.DoesNotExist:
        return f'#{user.pk}'
