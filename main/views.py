from django.shortcuts import render
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from .models import Testimonial



import json
import requests
from difflib import get_close_matches
from googletrans import Translator

from .models import Gallery, Booking, ChatData, UnknownQuestion


# 🌍 Translator
translator = Translator()


# =========================
# 🏠 HOME PAGE
# =========================
def home(request):
    images = Gallery.objects.all().order_by('-id')
    return render(request, "main/home.html", {"images": images})
def home(request):
    images = Gallery.objects.all().order_by('-id')
    testimonials = Testimonial.objects.filter(approved=True)

    return render(request, "main/home.html", {
        "images": images,
        "testimonials": testimonials
    })

# =========================
# 📸 CATEGORY API
# =========================
def get_category_images(request, category):
    images = Gallery.objects.filter(category=category)

    data = []
    for img in images:
        data.append({
            "image": img.image.url if img.image else None,
            "video": img.video.url if hasattr(img, 'video') and img.video else None,
            "title": img.title
        })

    return JsonResponse(data, safe=False)


# =========================
# 💾 SAVE BOOKING
# =========================
def save_booking(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        event = request.POST.get("event")
        event_date = request.POST.get("event_date")  # 🔥 FIX

        if not name or not phone or not event:
            return JsonResponse({"status": "error"})

        Booking.objects.create(
            name=name,
            phone=phone,
            event=event,
            event_date=event_date
        )

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"})


# =========================
# 📊 DASHBOARD
# =========================
def dashboard(request):
    bookings = Booking.objects.all().order_by('-created_at')

    total = Booking.objects.count()
    today = Booking.objects.filter(created_at__date=now().date()).count()

    event_data = Booking.objects.values('event').annotate(count=Count('event'))

    labels = [e['event'] for e in event_data]
    counts = [e['count'] for e in event_data]

    return render(request, "main/dashboard.html", {
        "bookings": bookings,
        "total": total,
        "today": today,
        "labels": json.dumps(labels),
        "counts": json.dumps(counts),
    })


# =========================
# 🤖 MULTI-LANGUAGE AI CHATBOT (FINAL)
# =========================
@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_msg_original = data.get("message", "")

            # 🌍 LANGUAGE DETECT
            detected = translator.detect(user_msg_original)
            user_lang = detected.lang

            # 🔄 TRANSLATE TO ENGLISH
            if user_lang != "en":
                user_msg = translator.translate(user_msg_original, dest="en").text.lower()
            else:
                user_msg = user_msg_original.lower()

            # =========================
            # 🔥 1. DATABASE MATCH
            # =========================
            all_data = ChatData.objects.all()
            questions = [item.question.lower() for item in all_data]

            match = get_close_matches(user_msg, questions, n=1, cutoff=0.6)

            if match:
                for item in all_data:
                    if item.question.lower() == match[0]:
                        answer = item.answer

                        # 🔄 TRANSLATE BACK
                        if user_lang != "en":
                            answer = translator.translate(answer, dest=user_lang).text

                        return JsonResponse({"reply": answer})

            # =========================
            # 🔥 2. SMART REPLIES
            # =========================
            if "booking" in user_msg:
                answer = "📅 Booking ke liye WhatsApp button use kare."

            elif "price" in user_msg or "charge" in user_msg:
                answer = "💰 Packages ₹25,000 se start hote hain."

            elif "foreign" in user_msg or "tourist" in user_msg:
                answer = "🌍 We provide full Indian wedding experience including stay, food, travel."

            else:
                answer = "🙏 Ask about booking, wedding or price."

            # 🔄 TRANSLATE BACK
            if user_lang != "en":
                answer = translator.translate(answer, dest=user_lang).text

            # =========================
            # 🧠 SAVE UNKNOWN
            # =========================
            UnknownQuestion.objects.create(question=user_msg)

            return JsonResponse({"reply": answer})

        except Exception as e:
            return JsonResponse({"reply": "Error, please try again."})

    return JsonResponse({"reply": "Invalid request"})
@csrf_exempt
def submit_feedback(request):
    if request.method == "POST":
        data = json.loads(request.body)

        Testimonial.objects.create(
            name=data.get("name"),
            message=data.get("message"),
            rating=data.get("rating", 5)
        )

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"})