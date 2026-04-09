from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('save-booking/', views.save_booking),

    path('category/<str:category>/', views.get_category_images),
    path('dashboard/', views.dashboard),

    # 🤖 chatbot
    path('chatbot/', views.chatbot_api),
    path('feedback/', views.submit_feedback),
]