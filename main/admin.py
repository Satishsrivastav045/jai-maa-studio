from urllib.parse import quote

from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from .models import Testimonial



from .models import Booking, ChatData, Gallery, LeadClick, Package, UnknownQuestion


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


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_label', 'highlighted', 'active', 'sort_order']
    list_filter = ['active', 'highlighted']
    list_editable = ['highlighted', 'active', 'sort_order']
    search_fields = ['name', 'description', 'features']


# =========================
# 🔥 BOOKING ADMIN
# =========================
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'event', 'event_date_value', 'status', 'lead_source', 'total_amount', 'advance_amount', 'balance_amount', 'payment_status', 'follow_up_date', 'created_at', 'whatsapp']
    search_fields = ['name', 'phone', 'event', 'lead_source']
    list_filter = ['event', 'status', 'payment_status', 'lead_source', 'event_date_value', 'follow_up_date', 'created_at']
    list_editable = ['status']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    # 💬 WhatsApp Button
    def whatsapp(self, obj):
        msg = f"Hello {obj.name}, your booking status is {obj.get_status_display()}."
        url = f"https://wa.me/91{obj.phone[-10:]}?text={quote(msg)}"
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
    list_display = ['question', 'keyword_preview', 'priority', 'active']
    list_filter = ['active']
    list_editable = ['priority', 'active']
    search_fields = ['question', 'keywords', 'answer']
    ordering = ['priority', 'id']

    def keyword_preview(self, obj):
        return ", ".join(obj.keyword_list()[:5]) or "-"

    keyword_preview.short_description = "Keywords"


# =========================
# 🧠 UNKNOWN QUESTIONS (LEARNING)
# =========================
@admin.register(UnknownQuestion)
class UnknownQuestionAdmin(admin.ModelAdmin):
    actions = ['create_training_answers']
    list_display = ['question', 'suggested_answer', 'trained', 'created_at']
    list_filter = ['trained']
    search_fields = ['question']
    ordering = ['-created_at']

    def create_training_answers(self, request, queryset):
        created = 0
        for item in queryset.filter(trained=False).exclude(suggested_answer__isnull=True).exclude(suggested_answer=""):
            ChatData.objects.create(
                question=item.question,
                keywords=item.question,
                answer=item.suggested_answer,
                priority=50,
            )
            item.trained = True
            item.save(update_fields=["trained"])
            created += 1
        self.message_user(request, f"{created} chatbot training answer(s) created.")

    create_training_answers.short_description = "Create ChatData from suggested answers"


@admin.register(LeadClick)
class LeadClickAdmin(admin.ModelAdmin):
    list_display = ['click_type', 'page', 'created_at']
    list_filter = ['click_type', 'created_at']
    readonly_fields = ['click_type', 'page', 'created_at']
admin.site.register(Testimonial)
