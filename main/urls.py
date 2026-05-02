from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('services/', views.services_page, name='services'),
    path('save-booking/', views.save_booking),
    path('check-availability/', views.check_availability),
    path('gallery/<str:category>/', views.gallery_view, name='gallery'),

    path('category/<str:category>/', views.get_category_images),
    path('dashboard/', views.dashboard),
    path('dashboard/bookings/<int:booking_id>/status/', views.update_booking_status),

    # 🤖 chatbot
    path('chatbot/', views.chatbot_api),
    path('feedback/', views.submit_feedback),
]
