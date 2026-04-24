from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # All skills app URLs live at the root — e.g. /skill/3/, /dashboard/
    path('', include('skills.urls')),
]
