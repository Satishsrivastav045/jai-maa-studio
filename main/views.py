import json
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from difflib import get_close_matches
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Booking, ChatData, Gallery, Testimonial, UnknownQuestion


def parse_event_date(value):
    value = (value or "").strip()
    if not value:
        return None

    for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    return None


# 🌍 Translator


def safe_detect_language(text):
    for ch in text:
        if '\u0900' <= ch <= '\u097F':
            return "hi"
    return "en"


def safe_translate(text, dest):
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
@ensure_csrf_cookie
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
@require_GET
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
@require_POST
def save_booking(request):
    name = request.POST.get("name", "").strip()
    phone = request.POST.get("phone", "").strip()
    event = request.POST.get("event", "").strip()
    event_date = request.POST.get("event_date", "").strip()

    if not name or not phone or not event or not event_date:
        return JsonResponse({"status": "error", "message": "Missing required fields"}, status=400)

    if not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
        return JsonResponse({"status": "error", "message": "Invalid phone number"}, status=400)

    booking = Booking.objects.create(
        name=name[:100],
        phone=phone,
        event=event[:100],
        event_date=event_date[:100],
        event_date_value=parse_event_date(event_date),
    )

    message = (
        "Hello, I want to book a shoot.\n"
        f"Name: {booking.name}\n"
        f"Phone: {booking.phone}\n"
        f"Event: {booking.event}\n"
        f"Date: {booking.event_date}"
    )
    whatsapp_url = f"https://wa.me/919936759702?text={quote(message)}"

    return JsonResponse({"status": "success", "whatsapp_url": whatsapp_url})


@require_GET
def check_availability(request):
    event_date = request.GET.get("event_date", "").strip()

    if not event_date:
        return JsonResponse({"status": "error", "message": "Event date is required"}, status=400)

    active_statuses = [Booking.STATUS_NEW, Booking.STATUS_CONFIRMED]
    parsed_date = parse_event_date(event_date)
    active_bookings = Booking.objects.filter(status__in=active_statuses)
    if parsed_date:
        active_bookings = active_bookings.filter(event_date_value=parsed_date)
    else:
        active_bookings = active_bookings.filter(event_date__iexact=event_date)
    available = not active_bookings.exists()

    if available:
        message = "Date available lag rahi hai. Booking confirm karne ke liye WhatsApp par details bhejein."
    else:
        message = "Is date par already inquiry/booking hai. Team final availability WhatsApp par confirm karegi."

    return JsonResponse({
        "status": "success",
        "available": available,
        "message": message,
        "active_booking_count": active_bookings.count(),
    })


# =========================
# 📊 DASHBOARD
# =========================
@login_required
def dashboard(request):
    bookings = Booking.objects.all()
    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    event_filter = request.GET.get("event", "").strip()
    date_from = parse_event_date(request.GET.get("date_from", ""))
    date_to = parse_event_date(request.GET.get("date_to", ""))

    if search:
        bookings = bookings.filter(
            Q(name__icontains=search)
            | Q(phone__icontains=search)
            | Q(event__icontains=search)
            | Q(notes__icontains=search)
        )

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    if event_filter:
        bookings = bookings.filter(event__icontains=event_filter)

    if date_from:
        bookings = bookings.filter(event_date_value__gte=date_from)

    if date_to:
        bookings = bookings.filter(event_date_value__lte=date_to)

    bookings = bookings.order_by('-created_at')

    total = Booking.objects.count()
    today = Booking.objects.filter(created_at__date=now().date()).count()
    confirmed = Booking.objects.filter(status=Booking.STATUS_CONFIRMED).count()
    pending_amount = Booking.objects.exclude(status=Booking.STATUS_CANCELLED).aggregate(
        total=Sum("advance_amount")
    )["total"] or 0

    event_data = bookings.values('event').annotate(count=Count('event'))

    labels = [e['event'] for e in event_data]
    counts = [e['count'] for e in event_data]

    return render(request, "main/dashboard.html", {
        "bookings": bookings,
        "total": total,
        "today": today,
        "confirmed": confirmed,
        "advance_total": pending_amount,
        "labels": json.dumps(labels),
        "counts": json.dumps(counts),
        "status_choices": Booking.STATUS_CHOICES,
        "filters": {
            "q": search,
            "status": status_filter,
            "event": event_filter,
            "date_from": request.GET.get("date_from", ""),
            "date_to": request.GET.get("date_to", ""),
        },
    })


@login_required
@require_POST
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    status = request.POST.get("status", "").strip()

    valid_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}
    if status not in valid_statuses:
        return JsonResponse({"status": "error", "message": "Invalid status"}, status=400)

    booking.status = status
    booking.save(update_fields=["status"])

    return JsonResponse({
        "status": "success",
        "booking_status": booking.status,
        "booking_status_label": booking.get_status_display(),
    })


@login_required
@require_POST
def update_booking_details(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    notes = request.POST.get("notes", "").strip()
    payment_status = request.POST.get("payment_status", "").strip()
    advance_amount = request.POST.get("advance_amount", "0").strip() or "0"

    try:
        parsed_amount = Decimal(advance_amount)
    except InvalidOperation:
        return JsonResponse({"status": "error", "message": "Invalid advance amount"}, status=400)

    if parsed_amount < 0:
        return JsonResponse({"status": "error", "message": "Advance amount cannot be negative"}, status=400)

    booking.notes = notes[:1000]
    booking.payment_status = payment_status[:50]
    booking.advance_amount = parsed_amount
    booking.save(update_fields=["notes", "payment_status", "advance_amount"])

    return JsonResponse({"status": "success", "message": "Booking details saved"})


@login_required
@require_GET
def export_bookings_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="bookings.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID",
        "Name",
        "Phone",
        "Event",
        "Event Date",
        "Status",
        "Advance Amount",
        "Payment Status",
        "Notes",
        "Created",
    ])

    for booking in Booking.objects.all().order_by("-created_at"):
        writer.writerow([
            booking.id,
            booking.name,
            booking.phone,
            booking.event,
            booking.event_date_value or booking.event_date,
            booking.get_status_display(),
            booking.advance_amount,
            booking.payment_status,
            booking.notes,
            booking.created_at,
        ])

    return response


# =========================
# 🤖 MULTI-LANGUAGE AI CHATBOT (FINAL)
# =========================
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body or "{}")
        user_msg = data.get("message", "").strip().lower()

        if not user_msg:
            return JsonResponse({"reply": "Please type a message."}, status=400)

        # =========================
        # 🔥 1. DATABASE MATCH
        # =========================
        all_data = ChatData.objects.all()
        questions = [item.question.lower() for item in all_data]

        match = get_close_matches(user_msg, questions, n=1, cutoff=0.6)

        if match:
            for item in all_data:
                if item.question.lower() == match[0]:
                    return JsonResponse({"reply": item.answer})

        # =========================
        # 🔥 2. STUDIO REPLY
        # =========================
        studio_answer = get_studio_reply(user_msg)
        if studio_answer:
            return JsonResponse({"reply": studio_answer})

        # =========================
        # 🔥 3. SMART REPLIES
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
                "Storytelling Collage aur Cinematic Full-Page layouts available hain."
            )

        else:
            answer = "🙏 Ask about booking, wedding, album design or price."

        # =========================
        # 🧠 SAVE UNKNOWN
        # =========================
        UnknownQuestion.objects.create(question=user_msg[:255])

        return JsonResponse({"reply": answer})

    except json.JSONDecodeError:
        return JsonResponse({"reply": "Invalid message format."}, status=400)



@require_POST
def submit_feedback(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    name = str(data.get("name", "")).strip()
    message = str(data.get("message", "")).strip()

    try:
        rating = int(data.get("rating", 5))
    except (TypeError, ValueError):
        rating = 5

    if not name or not message:
        return JsonResponse({"status": "error", "message": "Missing required fields"}, status=400)

    Testimonial.objects.create(
        name=name[:100],
        message=message,
        rating=max(1, min(rating, 5)),
    )

    return JsonResponse({"status": "success"})


@require_GET
def gallery_view(request, category):
    images = Gallery.objects.filter(category=category).order_by('-id')

    return render(request, "main/gallery.html", {
        "images": images,
        "category": category
    })
