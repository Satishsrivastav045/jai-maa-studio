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


def safe_detect_language(text):
    try:
        detected = translator.detect(text)
        return detected.lang if detected and detected.lang else "en"
    except Exception:
        return "en"


def safe_translate(text, dest):
    try:
        return translator.translate(text, dest=dest).text
    except Exception:
        return text


def get_studio_reply(user_msg):
    msg = user_msg.lower()

    if any(k in msg for k in ["working hours", "timing", "open", "available time", "time", "hours"]):
        return "🕘 Hum 9:00 AM se 9:00 PM tak available hain."

    if any(k in msg for k in ["service area", "area", "city", "village", "where do you work", "where are you from", "location"]):
        return (
            "📍 Wedding, pre-wedding, photography, videography, album design aur event coverage "
            "mainly Uttar Pradesh me available hai. Katha aur live streaming all over India available hai."
        )

    if any(k in msg for k in ["outstation", "destination", "travel", "outside city", "outside state"]):
        return "🚗 Haan, outstation shoot available hai. Travel, stay aur location-based charges apply ho sakte hain."

    if "drone" in msg:
        return "🚁 Drone service request ya custom package par available hai."

    if any(k in msg for k in ["live streaming", "streaming", "live video", "live katha", "katha"]):
        return "📡 Haan, live katha streaming karte hain. All over India coverage available hai."

    if any(k in msg for k in ["price", "pricing", "package", "cost", "charge", "rate", "fee", "pre-wedding kitne", "wedding kitne", "album kitne"]):
        return (
            "💰 Packages event, location aur coverage ke hisaab se custom hote hain. "
            "Photography packages generally ₹25,000 se start hote hain. "
            "Photo + video, pre-wedding, album design, drone, extra hours, travel aur outstation charges alag ho sakte hain."
        )

    if any(k in msg for k in ["services list", "services do", "what services", "services", "dete ho", "offer", "provide"]):
        return (
            "🎬 Hum pre-wedding shoot, wedding photography, wedding videography, candid photography, "
            "cinematic video, album design, live katha streaming aur all types of event coverage provide karte hain."
        )

    if any(k in msg for k in ["photographer", "photographers", "team", "crew", "kitne photographer"]):
        return "📸 Team size event aur package ke hisaab se decide hota hai. Usually photographer aur videographer ki proper team available hoti hai."

    if any(k in msg for k in ["booking", "book", "advance", "payment", "confirm", "cancel", "refund"]):
        return (
            "📅 Booking WhatsApp ya call par hoti hai. Date lock karne ke liye advance required hota hai. "
            "Payment UPI, cash ya bank transfer se le sakte hain. Booking advance receive hone par confirm hoti hai. "
            "Cancellation/refund policy case-to-case basis par discuss ki jaati hai."
        )

    if any(k in msg for k in ["delivery", "deliver", "raw photo", "raw video", "album ready", "photos kitne din", "video kitne din"]):
        return (
            "📦 Photos, video aur album ki delivery project size aur season ke hisaab se hoti hai. "
            "Usually photos 7-15 working days, video 15-30 working days aur album 30-45 days me ready ho jata hai. "
            "Raw photos/video request ya package ke hisaab se share kiye ja sakte hain."
        )

    if any(k in msg for k in ["album me kitni photos", "album photos", "album pages", "album size"]):
        return (
            "📒 Album me photos aur pages package aur album size ke hisaab se customize hote hain. "
            "Final count shoot coverage aur selected album design par depend karta hai."
        )

    if any(k in msg for k in ["wedding", "engagement", "haldi", "mehndi", "birthday", "katha", "other functions", "function", "event"]):
        return (
            "✨ Wedding, engagement, haldi, mehndi, birthday, katha aur other family events sab cover karte hain. "
            "Har event ke liye custom package available hai."
        )

    if any(k in msg for k in ["whatsapp", "contact", "call", "number", "how to contact"]):
        return "📲 WhatsApp par directly contact karke booking aur details le sakte hain."

    if any(k in msg for k in ["album me kitni photos", "album pages", "album design", "photo book", "album"]):
        return (
            "📒 Album design me Classic Royal, Minimal Premium, Storytelling Collage aur Cinematic Full-Page layouts available hain. "
            "Album me photos aur pages package ke hisaab se decide hote hain."
        )

    if any(k in msg for k in ["language", "tone", "reply style", "short reply", "detailed"]):
        return "💬 Reply Hindi/Hinglish me friendly aur simple style me diya jata hai. Zarurat par short ya detailed dono type ke answers mil sakte hain."

    if any(k in msg for k in ["fake promise", "don’t know", "dont know", "uncertain", "avoid"]):
        return "✅ Agar koi detail confirm nahi hoti, to hum fake promise nahi karte aur booking time par final information share karte hain."

    return None


# =========================
# 🏠 HOME PAGE
# =========================
def home(request):
    images = (
        Gallery.objects.filter(image__isnull=False)
        .exclude(image="")
        .order_by('-id')[:8]
    )
    testimonials = Testimonial.objects.filter(approved=True)

    return render(request, "main/home.html", {
        "images": images,
        "testimonials": testimonials
    })


def services_page(request):
    return render(request, "main/services.html")

# =========================
# 📸 CATEGORY API
# =========================
def get_category_images(request, category):
    images = Gallery.objects.filter(category=category).order_by('-id')

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
            user_lang = safe_detect_language(user_msg_original)

            # 🔄 TRANSLATE TO ENGLISH
            if user_lang != "en":
                user_msg = safe_translate(user_msg_original, dest="en").lower()
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
                            answer = safe_translate(answer, dest=user_lang)

                        return JsonResponse({"reply": answer})

            studio_answer = get_studio_reply(user_msg)
            if studio_answer:
                if user_lang != "en":
                    studio_answer = safe_translate(studio_answer, dest=user_lang)
                return JsonResponse({"reply": studio_answer})

            # =========================
            # 🔥 2. SMART REPLIES
            # =========================
            if "booking" in user_msg:
                answer = "📅 Booking ke liye WhatsApp button use kare."

            elif "price" in user_msg or "charge" in user_msg:
                answer = "💰 Packages ₹25,000 se start hote hain."

            elif "foreign" in user_msg or "tourist" in user_msg:
                answer = "🌍 We provide full Indian wedding experience including stay, food, travel."

            elif (
                "album" in user_msg
                or "photobook" in user_msg
                or "layout" in user_msg
                or "cover" in user_msg
                or "pages" in user_msg
            ):
                answer = (
                    "📒 Album design me Classic Royal, Minimal Premium, "
                    "Storytelling Collage aur Cinematic Full-Page layouts available hain. "
                    "Aap photos bhejo, hum print-ready album design bana denge."
                )

            else:
                answer = "🙏 Ask about booking, wedding, album design or price."

            # 🔄 TRANSLATE BACK
            if user_lang != "en":
                answer = safe_translate(answer, dest=user_lang)

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
def gallery_view(request, category):
    images = Gallery.objects.filter(category=category).order_by('-id')

    return render(request, "main/gallery.html", {
        "images": images,
        "category": category
    })
