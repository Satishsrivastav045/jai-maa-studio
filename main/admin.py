from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from .models import Testimonial



from .models import Gallery, Booking, ChatData, UnknownQuestion


# =========================
# 🔥 GALLERY ADMIN
# =========================
@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['id', 'preview', 'title', 'category']
    list_filter = ['category']
    search_fields = ['title']

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="60" style="border-radius:5px;" />',
                obj.image.url
            )
        return "No Image"

    preview.short_description = "Preview"


# =========================
# 🔥 BOOKING ADMIN
# =========================
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'event', 'event_date', 'created_at', 'whatsapp']
    search_fields = ['name', 'phone', 'event']
    list_filter = ['event', 'created_at']
    ordering = ['-created_at']

    # 💬 WhatsApp Button
    def whatsapp(self, obj):
        msg = f"Hello {obj.name}, your booking is confirmed."
        url = f"https://wa.me/{obj.phone}?text={msg}"
        return format_html(
            '<a href="{}" target="_blank" style="color:green;">💬 WhatsApp</a>',
            url
        )

    whatsapp.short_description = "Contact"

    # 📊 Dashboard Stats
    def changelist_view(self, request, extra_context=None):
        today = now().date()

        total = Booking.objects.count()
        today_count = Booking.objects.filter(created_at__date=today).count()

        extra_context = extra_context or {}
        extra_context['total_bookings'] = total
        extra_context['today_bookings'] = today_count

        return super().changelist_view(request, extra_context=extra_context)


# =========================
# 🤖 CHAT DATA (TRAINING)
# =========================
@admin.register(ChatData)
class ChatDataAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer']
    search_fields = ['question']


# =========================
# 🧠 UNKNOWN QUESTIONS (LEARNING)
# =========================
@admin.register(UnknownQuestion)
class UnknownQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'suggested_answer', 'created_at']
    search_fields = ['question']
    ordering = ['-created_at']
admin.site.register(Testimonial)