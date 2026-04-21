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


# =========================
# 📅 BOOKING
# =========================
class Booking(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=11)
    event = models.CharField(max_length=100)
    event_date = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================
# 🤖 CHATBOT DATA (TRAINING)
# =========================
class ChatData(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question


# =========================
# 🧠 UNKNOWN QUESTIONS (LEARNING)
# =========================
class UnknownQuestion(models.Model):
    question = models.CharField(max_length=255)
    suggested_answer = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question
class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    message = models.TextField()
    rating = models.IntegerField(default=5)
    approved = models.BooleanField(default=False)  # 🔥 admin approve

    def __str__(self):
        return self.name