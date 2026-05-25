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
    path('dashboard/bookings/<int:booking_id>/details/', views.update_booking_details),
    path('dashboard/export/', views.export_bookings_csv),
    path('dashboard/backup/', views.export_backup_json),
    path('track-click/', views.track_click),
    path('seo/<slug:slug>/', views.seo_page, name='seo_page'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('security-code/', views.admin_security_code, name='admin_security_code'),

    # 🤖 chatbot
    path('chatbot/', views.chatbot_api),
    path('feedback/', views.submit_feedback),
]
