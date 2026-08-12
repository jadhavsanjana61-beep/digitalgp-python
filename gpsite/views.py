import base64
from io import BytesIO

import qrcode
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import models
from .forms import GpLoginForm, TicketForm
from .media_utils import compress_image, compress_video


def _base_template(request):
    return f"{request.tenant_template}/base.html"


def _require_tenant(request):
    if request.tenant is None:
        raise Http404("No tenant resolved for this host.")


def home_view(request):
    """
    Renders the resolved tenant's homepage, or (when no tenant is resolved --
    the base domain / an unrecognised host) a small dev picker page listing
    every registered Gram Panchayat so you can switch tenants locally without
    touching DNS or the Windows hosts file.
    """
    if request.tenant is None:
        from .marketing_views import landing_view
        return landing_view(request)

    tenant = request.tenant
    suvichar = models.Suvichar.objects.filter(register=tenant).order_by("-id").first()
    announcements = models.Announcement.objects.filter(register=tenant).order_by("-date")[:4]
    slides = models.ImageSlider.objects.filter(register=tenant).order_by("-id")[:6]
    about = models.AboutUs.objects.filter(register=tenant).first()
    events = models.EventMaster.objects.filter(register=tenant).order_by("-event_date")[:4]
    awards = models.Award.objects.filter(register=tenant).order_by("-id")[:3]
    vitarit_dakhle = models.VitaritDakhle.objects.filter(register=tenant).order_by("-id").first()
    gallery = models.Gallery.objects.filter(register=tenant).order_by("-id")[:8]

    return render(request, "content/home.html", {
        "gp": tenant,
        "base_template": _base_template(request),
        "suvichar": suvichar,
        "announcements": announcements,
        "slides": slides,
        "about": about,
        "events": events,
        "awards": awards,
        "vitarit_dakhle": vitarit_dakhle,
        "gallery": gallery,
    })


def switch_tenant(request):
    """Dev-only helper: clears the simulated subdomain and returns to the picker page."""
    request.session.pop("dev_subdomain", None)
    return redirect("home")


# ---------------------------------------------------------------------------
# About Us / History
# ---------------------------------------------------------------------------

def about_us_view(request):
    _require_tenant(request)
    about = models.AboutUs.objects.filter(register=request.tenant).first()
    images = list(about.details.values_list("image_url", flat=True)) if about else []
    return render(request, "content/gallery_detail.html", {
        "gp": request.tenant,
        "base_template": _base_template(request),
        "page_title": "आमच्याविषयी",
        "description": about.description if about else "अजून माहिती जोडलेली नाही.",
        "images": images,
        "back_link": "/",
    })


def history_view(request):
    _require_tenant(request)
    qs = models.History.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {
            "title": (h.history_desc[:60] if h.history_desc else f"नोंद #{h.id}"),
            "description": h.history_desc,
            "image_url": h.image_url,
        }
        for h in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "इतिहास", "items": items,
    })


# ---------------------------------------------------------------------------
# Announcements / Gallery
# ---------------------------------------------------------------------------

def announcements_view(request):
    _require_tenant(request)
    qs = models.Announcement.objects.filter(register=request.tenant).order_by("-date")
    items = [
        {"title": a.title, "description": a.description, "date": a.date, "image_url": a.image_url}
        for a in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "घोषणा", "items": items,
    })


def gallery_view(request):
    _require_tenant(request)
    qs = models.Gallery.objects.filter(register=request.tenant).select_related("image_type").order_by("-id")
    items = [
        {
            "title": g.image_title,
            "subtitle": g.image_type.image_type_name if g.image_type else None,
            "image_url": g.image_url,
        }
        for g in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "छायाचित्र दालन", "items": items,
    })


# ---------------------------------------------------------------------------
# Events / Awards (master-detail: each has its own image gallery)
# ---------------------------------------------------------------------------

def events_view(request):
    _require_tenant(request)
    qs = models.EventMaster.objects.filter(register=request.tenant).order_by("-event_date")
    items = []
    for e in qs:
        items.append({
            "title": e.event_name,
            "description": e.event_desc,
            "date": e.event_date,
            "image_url": e.details.values_list("image_url", flat=True).first(),
            "link": f"/events/{e.id}/",
            "link_label": "फोटो बघा",
        })
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "कार्यक्रम", "items": items,
    })


def event_detail_view(request, pk):
    _require_tenant(request)
    event = get_object_or_404(models.EventMaster, pk=pk, register=request.tenant)
    return render(request, "content/gallery_detail.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": event.event_name,
        "subtitle": event.event_date,
        "description": event.event_desc,
        "images": list(event.details.values_list("image_url", flat=True)),
        "back_link": "/events/",
    })


def awards_view(request):
    _require_tenant(request)
    qs = models.Award.objects.filter(register=request.tenant).order_by("-id")
    items = []
    for a in qs:
        items.append({
            "title": a.award_name,
            "description": a.award_des,
            "subtitle": a.award_date,
            "image_url": a.details.values_list("img_url", flat=True).first(),
            "link": f"/awards/{a.id}/",
            "link_label": "फोटो बघा",
        })
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "पुरस्कार", "items": items,
    })


def award_detail_view(request, pk):
    _require_tenant(request)
    award = get_object_or_404(models.Award, pk=pk, register=request.tenant)
    return render(request, "content/gallery_detail.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": award.award_name,
        "subtitle": award.award_date,
        "description": award.award_des,
        "images": list(award.details.values_list("img_url", flat=True)),
        "back_link": "/awards/",
    })


# ---------------------------------------------------------------------------
# Officials / members
# ---------------------------------------------------------------------------

def grampanchayat_body_view(request):
    _require_tenant(request)
    qs = models.GrampanchayatBody.objects.filter(register=request.tenant).select_related("position").order_by("id")
    items = [
        {
            "title": m.name,
            "subtitle": m.position.position_name if m.position else None,
            "image_url": m.image_url,
        }
        for m in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "पदाधिकारी", "items": items,
    })


def leadership_view(request):
    _require_tenant(request)
    qs = models.LeadershipMember.objects.filter(register=request.tenant).order_by("id")
    items = [
        {"title": m.name, "subtitle": m.designation, "image_url": m.image_url}
        for m in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "नेतृत्व", "items": items,
    })


# ---------------------------------------------------------------------------
# Finance / RTI / Schemes
# ---------------------------------------------------------------------------

def jama_kharch_view(request):
    _require_tenant(request)
    qs = models.JamaKharchPatrak.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {
            "title": j.jama_kharch_nav,
            "description": (
                f"जमा: ₹{j.jama_rakkam or 0} | "
                f"खर्च: ₹{j.kharch_rakkam or 0} | "
                f"शिल्लक: ₹{j.shillak_rakkam or 0}"
            ),
            "link": j.pdf_url,
            "link_label": "PDF बघा",
        }
        for j in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "जमा-खर्च पत्रक", "items": items,
    })


def mahiti_adhikar_view(request):
    _require_tenant(request)
    qs = models.MahitiAdhikar.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {
            "title": m.browse_uri or f"दस्तऐवज #{m.id}",
            "image_url": m.browse_image,
            "link": m.pdf_file,
            "link_label": "PDF बघा",
        }
        for m in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "माहिती अधिकार", "items": items,
    })


def yojana_view(request):
    _require_tenant(request)
    qs = models.YojnaDetail.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {
            "title": y.yojana_name,
            "description": y.description,
            "image_url": y.logo_image_url,
            "link": y.website_link or y.browse_pdf,
            "link_label": "अधिक माहिती",
        }
        for y in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "शासकीय योजना", "items": items,
    })


# ---------------------------------------------------------------------------
# Tourism / notable persons / schools / missions
# ---------------------------------------------------------------------------

def tourist_gallery_view(request):
    _require_tenant(request)
    qs = models.TouristGallery.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {"title": t.paryatan_name, "description": t.description, "image_url": t.image_url}
        for t in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "पर्यटन दालन", "items": items,
    })


def gauravshalivyakti_view(request):
    _require_tenant(request)
    qs = models.Gauravshalivyakti.objects.filter(register=request.tenant).select_related("category").order_by("-id")
    items = [
        {
            "title": g.name,
            "subtitle": g.category.category if g.category else None,
            "description": g.description,
            "image_url": g.image_url,
        }
        for g in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "गौरवशाली व्यक्ती", "items": items,
    })


def village_schools_view(request):
    _require_tenant(request)
    qs = models.VillageSchool.objects.filter(register=request.tenant).order_by("id")
    items = [
        {
            "title": s.school_name,
            "subtitle": f"मुले: {s.total_boys or 0} | मुली: {s.total_girls or 0} | शिक्षक: {s.total_teachers or 0}",
            "description": s.school_address,
            "image_url": s.school_photo_url,
        }
        for s in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "गावातील शाळा", "items": items,
    })


def swachh_bharat_view(request):
    _require_tenant(request)
    qs = models.SwachhBharatMission.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {"title": s.title, "description": s.description, "image_url": s.image_url}
        for s in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "स्वच्छ भारत मिशन", "items": items,
    })


def panchayat_raj_mission_view(request):
    _require_tenant(request)
    qs = models.PanchayatRajMission.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {"title": p.title, "description": p.description, "image_url": p.img, "link": p.url, "link_label": "अधिक माहिती"}
        for p in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "पंचायत राज मिशन", "items": items,
    })


# ---------------------------------------------------------------------------
# Certificates issued (stats) / UPI QR / citizen complaint form
# ---------------------------------------------------------------------------

def vitarit_dakhle_view(request):
    _require_tenant(request)
    record = models.VitaritDakhle.objects.filter(register=request.tenant).order_by("-id").first()
    stats = []
    if record:
        stats = [
            ("जन्म दाखले", record.janm_dakhale),
            ("मृत्यू दाखले", record.mrutu_dakhale),
            ("विवाह दाखले", record.vivah_dakhale),
            ("दारिद्र्य रेषेखालील दाखले", record.daridrya_reshe_khalil_dakhale),
            ("थकबाकी नसल्याचे दाखले", record.thak_baki_naslyache_dakhale),
            ("निराधार योजना दाखले", record.niradhar_yojna_dakhale),
            ("रहिवासी दाखले", record.rahivashi_dakhale),
        ]
    return render(request, "content/stats.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "वितरित दाखले", "stats": stats,
    })


def _qr_base64(data):
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def upi_details_view(request):
    _require_tenant(request)
    record = models.UpiDetailsMaster.objects.filter(register=request.tenant).order_by("-id").first()
    upi = None
    if record:
        upi = {
            "gharpatti_upi_id": record.gharpatti_upi_id,
            "gharpatti_account_holder_name": record.gharpatti_account_holder_name,
            "panipatti_upi_id": record.panipatti_upi_id,
            "panipatti_account_holder_name": record.panipatti_account_holder_name,
            "gharpatti_qr": _qr_base64(
                f"upi://pay?pa={record.gharpatti_upi_id}&pn={record.gharpatti_account_holder_name}&cu=INR"
            ) if record.gharpatti_upi_id else None,
            "panipatti_qr": _qr_base64(
                f"upi://pay?pa={record.panipatti_upi_id}&pn={record.panipatti_account_holder_name}&cu=INR"
            ) if record.panipatti_upi_id else None,
        }
    return render(request, "content/upi.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "ऑनलाईन कर भरणा (UPI)", "upi": upi,
    })


def ticket_view(request):
    _require_tenant(request)
    submitted = False
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            takrar_img = takrar_url = None
            photo = form.cleaned_data.get("photo")
            if photo:
                compressed = compress_image(photo, filename_hint=photo.name)
                saved_path = default_storage.save(f"tickets/{compressed.name}", compressed)
                takrar_img = compressed.name
                takrar_url = default_storage.url(saved_path)

            models.Ticket.objects.create(
                register=request.tenant,
                name=form.cleaned_data["name"],
                mobile_number=form.cleaned_data["mobile_number"],
                reason=form.cleaned_data["reason"],
                message=form.cleaned_data["message"],
                status="Open",
                created_on=timezone.now(),
                takrar_img=takrar_img,
                takrar_url=takrar_url,
            )
            submitted = True
            form = TicketForm()
    else:
        form = TicketForm()
    return render(request, "content/ticket_form.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "form": form, "submitted": submitted,
    })


# ---------------------------------------------------------------------------
# Member history / administrative officials / divisions
# ---------------------------------------------------------------------------

def all_member_history_view(request):
    _require_tenant(request)
    qs = models.AllMemberHistory.objects.filter(register=request.tenant).select_related("position").order_by("-start_year")
    items = [
        {
            "title": m.name,
            "subtitle": m.position.position_name if m.position else None,
            "description": f"{m.start_year or '—'} ते {m.end_year or '—'}",
            "image_url": m.image_url,
        }
        for m in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "सदस्य इतिहास", "items": items,
    })


def prashaskiy_adhikari_view(request):
    _require_tenant(request)
    qs = models.PrashaskiyAdhikari.objects.filter(register=request.tenant).select_related("position").order_by("id")
    items = [
        {
            "title": p.adhikari_name,
            "subtitle": p.position.position_name if p.position else None,
            "description": f"मोबाईल: {p.mobile_no or '—'} | दूरध्वनी: {p.tele_phone_no or '—'}",
            "image_url": p.image_url,
        }
        for p in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "प्रशासकीय अधिकारी", "items": items,
    })


def prashaskiy_vibhag_view(request):
    _require_tenant(request)
    qs = models.PrashaskiyVibhagP.objects.filter(register=request.tenant).order_by("id")
    items = [
        {"title": v.zpgat, "description": f"पं.स. गण: {v.ps_gan1 or '—'}, {v.ps_gan2 or '—'}"}
        for v in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "प्रशासकीय विभाग (झेडपी गट / पंसं गण)", "items": items,
    })


def jababdari_bhumika_view(request):
    _require_tenant(request)
    qs = models.JababdariBhumika.objects.filter(position__register=request.tenant).select_related("position").order_by("id")
    items = [
        {
            "title": j.position.position_name if j.position else f"जबाबदारी #{j.id}",
            "description": f"भूमिका: {j.bhumika or '—'} | जबाबदारी: {j.jababdari or '—'}",
        }
        for j in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "जबाबदारी व भूमिका", "items": items,
    })


def vibhagiya_ayukta_view(request):
    _require_tenant(request)
    # NOTE: this table has no RegisterId in the original schema -- it's shared
    # reference data (Divisional Commissioner info) rather than per-tenant content.
    qs = models.VibhagiyaAyukta.objects.all().order_by("id")
    items = [
        {"title": v.name, "subtitle": v.vibhag, "description": v.padh, "image_url": v.img, "link": v.url, "link_label": "अधिक माहिती"}
        for v in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "विभागीय आयुक्त", "items": items,
    })


def aptkalin_contact_view(request):
    _require_tenant(request)
    qs = models.AptkalinContact.objects.filter(register=request.tenant).order_by("id")
    items = [
        {"title": a.vibhag_name, "description": f"मोबाईल: {a.mobile_no or '—'} | दूरध्वनी: {a.telephone_no or '—'}"}
        for a in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "आपत्कालीन संपर्क", "items": items,
    })


def shasan_nirnay_view(request):
    _require_tenant(request)
    # NOTE: this table has no RegisterId in the original schema -- Government
    # Resolutions are state-level reference documents, not per-tenant content.
    qs = models.ShasanNirnay.objects.all().order_by("-id")
    items = [
        {"title": s.shasan_nirnay_name, "image_url": s.browse_image, "link": s.browse_uri, "link_label": "PDF बघा"}
        for s in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "शासन निर्णय", "items": items,
    })


def gram_vikas_kame_view(request):
    _require_tenant(request)
    qs = models.GramVikasKame.objects.filter(register=request.tenant).order_by("-id")
    items = []
    for g in qs:
        items.append({
            "title": g.work_name,
            "subtitle": g.yojna_name,
            "description": f"मंजूर निधी: ₹{g.manjur_nidhi or 0} | खर्च निधी: ₹{g.kharch_nidhi or 0} | स्थिती: {g.status or '—'}",
            "image_url": g.details.values_list("image_url", flat=True).first(),
            "link": f"/gram-vikas-kame/{g.id}/",
            "link_label": "फोटो बघा",
        })
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "ग्रामविकास कामे", "items": items,
    })


def gram_vikas_kame_detail_view(request, pk):
    _require_tenant(request)
    work = get_object_or_404(models.GramVikasKame, pk=pk, register=request.tenant)
    return render(request, "content/gallery_detail.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": work.work_name,
        "subtitle": work.yojna_name,
        "description": f"मंजूर निधी: ₹{work.manjur_nidhi or 0} | खर्च निधी: ₹{work.kharch_nidhi or 0} | स्थिती: {work.status or '—'}",
        "images": list(work.details.values_list("image_url", flat=True)),
        "back_link": "/gram-vikas-kame/",
    })


def gp_login_view(request):
    """
    Admin login -- works two ways, matching how the original app's root-level
    /Login page could authenticate a user regardless of which subdomain they
    arrived from:

    - Reached from a resolved tenant subdomain: credentials must belong to
      THAT tenant (or be a superuser).
    - Reached from the base/marketing domain (no tenant resolved): any valid
      account works: the user's own tenant is looked up from their profile
      and the dev-subdomain override is set so the rest of the session
      resolves into their site, then they land on /dashboard/.
    """
    error = None
    if request.method == "POST":
        form = GpLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            profile = getattr(user, "gp_profile", None) if user else None
            if user is None:
                error = "युजरनेम किंवा पासवर्ड चुकीचा आहे."
            elif request.tenant is not None and not user.is_superuser and (
                profile is None or profile.register_id != request.tenant.id
            ):
                error = "हे खाते या Gram Panchayat साठी नाही."
            else:
                auth_login(request, user)
                if request.tenant is None:
                    if profile is None:
                        # Superuser with no tenant profile logging in from the
                        # base domain -> there's no single tenant dashboard to
                        # send them to, so land on the platform's own GP list.
                        return redirect("platform_dashboard")
                    subdomain = profile.register.subdomaindetail_set.first()
                    if subdomain:
                        request.session["dev_subdomain"] = subdomain.subdomain
                return redirect("dashboard")
    else:
        form = GpLoginForm()

    if request.tenant is None:
        return render(request, "marketing/login.html", {"form": form, "error": error})
    return render(request, "content/login.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "form": form, "error": error,
    })


def gp_logout_view(request):
    auth_logout(request)
    return redirect("home")


@login_required(login_url="/login/")
def dashboard_view(request):
    _require_tenant(request)
    profile = getattr(request.user, "gp_profile", None)
    if not request.user.is_superuser and (profile is None or profile.register_id != request.tenant.id):
        auth_logout(request)
        return redirect("gp_login")

    tenant = request.tenant
    stats = [
        ("घोषणा", models.Announcement.objects.filter(register=tenant).count()),
        ("छायाचित्रे", models.Gallery.objects.filter(register=tenant).count()),
        ("कार्यक्रम", models.EventMaster.objects.filter(register=tenant).count()),
        ("प्रलंबित तक्रारी", models.Ticket.objects.filter(register=tenant, status="Open").count()),
        ("एकूण तक्रारी", models.Ticket.objects.filter(register=tenant).count()),
    ]
    return render(request, "content/dashboard.html", {
        "gp": tenant, "base_template": _base_template(request),
        "stats": stats, "role": profile.role if profile else "Superuser",
    })


def other_history_view(request):
    _require_tenant(request)
    qs = models.OtherHistory.objects.filter(register=request.tenant).order_by("-id")
    items = [
        {"title": o.title, "description": o.description, "image_url": o.image_url}
        for o in qs
    ]
    return render(request, "content/generic_list.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "इतर ऐतिहासिक नोंदी", "items": items,
    })


def videos_view(request):
    _require_tenant(request)
    qs = models.Video.objects.filter(register=request.tenant).order_by("-id")
    return render(request, "content/videos.html", {
        "gp": request.tenant, "base_template": _base_template(request),
        "page_title": "व्हिडिओ गॅलरी", "videos": qs,
    })
