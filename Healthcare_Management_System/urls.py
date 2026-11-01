from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),                    # Home page (NEW)
    path('users/', include('users.urls')),             # User auth
    path('appointments/', include('appointments.urls')),# Appointments
    path('chatbot/', include('chatbot.urls')),         # Chatbot
]
