from django.db import models


# =========================
# 📸 GALLERY (IMAGE + VIDEO)
# =========================
class Gallery(models.Model):
    CATEGORY_CHOICES = [
        ('prewedding', 'Pre Wedding'),
        ('candid', 'Candid'),
        ('fineart', 'Fine Art'),
        ('video', 'Video'),
        ('traditional', 'Traditional Video'),
        ('cinematic', 'Cinematic Highlights'),
        ('katha', 'Live Katha Streaming'),
        ('album', 'Wedding Album Design'),
    ]

    image = models.ImageField(upload_to='gallery/', null=True, blank=True)
    video = models.FileField(upload_to='videos/', null=True, blank=True)

    title = models.CharField(max_length=100, blank=True)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='prewedding'
    )

    def __str__(self):
        return self.title if self.title else self.category


class Package(models.Model):
    name = models.CharField(max_length=100)
    price_label = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    features = models.TextField(
        blank=True,
        help_text="Add one package feature per line.",
    )
    cta_label = models.CharField(max_length=50, default="Choose Package")
    event_name = models.CharField(max_length=100, blank=True)
    highlighted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

    def feature_list(self):
        return [feature.strip() for feature in self.features.splitlines() if feature.strip()]


# =========================
# 📅 BOOKING
# =========================
class Booking(models.Model):
    STATUS_NEW = "new"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CONTACTED = "contacted"
    STATUS_LOST = "lost"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_LOST, "Lost"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    event = models.CharField(max_length=100)
    event_date = models.CharField(max_length=100)
    event_date_value = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    notes = models.TextField(blank=True)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=50, blank=True, default="Pending")
    lead_source = models.CharField(max_length=100, blank=True, default="Website")
    follow_up_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance_amount(self):
        balance = self.total_amount - self.advance_amount
        return balance if balance > 0 else 0

    def __str__(self):
        return self.name


# =========================
# 🤖 CHATBOT DATA (TRAINING)
# =========================
class ChatData(models.Model):
    question = models.CharField(max_length=255)
    keywords = models.TextField(
        blank=True,
        help_text="Comma or line separated words/phrases that should trigger this answer.",
    )
    answer = models.TextField()
    active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(
        default=100,
        help_text="Lower number is checked first.",
    )

    class Meta:
        ordering = ["priority", "id"]

    def __str__(self):
        return self.question

    def keyword_list(self):
        raw_keywords = self.keywords.replace("\n", ",").split(",")
        return [keyword.strip() for keyword in raw_keywords if keyword.strip()]


# =========================
# 🧠 UNKNOWN QUESTIONS (LEARNING)
# =========================
class UnknownQuestion(models.Model):
    question = models.CharField(max_length=255)
    suggested_answer = models.TextField(blank=True, null=True)
    trained = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class LeadClick(models.Model):
    TYPE_WHATSAPP = "whatsapp"
    TYPE_CALL = "call"
    TYPE_YOUTUBE = "youtube"
    TYPE_INSTAGRAM = "instagram"

    TYPE_CHOICES = [
        (TYPE_WHATSAPP, "WhatsApp"),
        (TYPE_CALL, "Call"),
        (TYPE_YOUTUBE, "YouTube"),
        (TYPE_INSTAGRAM, "Instagram"),
    ]

    click_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    page = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_click_type_display()} - {self.created_at:%Y-%m-%d}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    message = models.TextField()
    rating = models.IntegerField(default=5)
    approved = models.BooleanField(default=False)  # 🔥 admin approve

    def __str__(self):
        return self.name
