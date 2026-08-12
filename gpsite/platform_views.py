"""
Platform-level views: not tied to any single Gram Panchayat's subdomain.
Only the platform superuser (the one who provisions new villages) can reach
these -- a village-level GP admin never sees this, same separation as the
SuperuserOnlyModelAdmin tables in admin.py.
"""

import json
import secrets
import string

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render

from . import models
from .maharashtra_locations import MAHARASHTRA_DISTRICTS_TALUKAS
from .platform_forms import RegisterGpForm

DISTRICTS_TALUKAS_JSON = json.dumps(MAHARASHTRA_DISTRICTS_TALUKAS)

is_superuser = user_passes_test(lambda u: u.is_superuser, login_url="/admin/login/")


def _username_from_mobile(contact_no):
    """Login username = the mobile number itself, matching the original
    app's TblUserInfo.UserName = ContactNo. A numeric suffix only kicks in
    on the unlikely collision of a stray User already holding that username."""
    username = contact_no
    n = 1
    while User.objects.filter(username=username).exists():
        n += 1
        username = f"{contact_no}-{n}"
    return username


def _generate_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@login_required(login_url="/admin/login/")
@is_superuser
def register_gp_view(request):
    created = None
    if request.method == "POST":
        form = RegisterGpForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            registration = models.Registration.objects.create(
                gram_panchayat_name=data["gram_panchayat_name"],
                gram_panchayat_name_en=data["gram_panchayat_name_en"],
                taluka=data["taluka"],
                district=data["district"],
                contact_no=data["contact_no"],
                template=data["template"],
                status=True,
            )
            models.SubdomainDetail.objects.create(
                register=registration, subdomain=data["subdomain"],
            )
            username = _username_from_mobile(data["contact_no"])
            password = _generate_password()
            user = User.objects.create_user(username=username, password=password, is_staff=True)
            models.UserInfo.objects.create(
                user=user, register=registration, role=models.UserInfo.ROLE_ADMIN,
            )
            created = {
                "gp": registration, "subdomain": data["subdomain"],
                "username": username, "password": password,
            }
            form = RegisterGpForm()
    else:
        form = RegisterGpForm()
    return render(request, "platform/register_gp.html", {
        "form": form, "created": created,
        "districts_talukas_json": DISTRICTS_TALUKAS_JSON,
    })


@login_required(login_url="/admin/login/")
@is_superuser
def gp_list_view(request):
    registrations = models.Registration.objects.prefetch_related("subdomaindetail_set").order_by("-id")
    return render(request, "platform/gp_list.html", {"registrations": registrations})


@login_required(login_url="/admin/login/")
@is_superuser
def dashboard_view(request):
    """
    Platform superuser's dashboard home -- stat cards mirroring the original
    AdminDashboard.razor's counters (Total Registrations/Subdomains,
    Available Templates, per-template registration counts). The original
    also showed a "Global Traffic Overview" panel sourced from Google
    Analytics (GA4) -- there are no GA4 credentials for this project, so
    that's replaced with a real internal "site summary" instead of faking
    traffic numbers.
    """
    total_registrations = models.Registration.objects.count()
    total_subdomains = models.SubdomainDetail.objects.count()
    template_counts = [
        ("Template1", models.Registration.objects.filter(template="Template1").count()),
        ("Template2", models.Registration.objects.filter(template="Template2").count()),
        ("Template3", models.Registration.objects.filter(template="Template3").count()),
    ]
    site_summary = [
        ("एकूण तक्रारी (सर्व गावं)", models.Ticket.objects.count()),
        ("एकूण घोषणा", models.Announcement.objects.count()),
        ("एकूण छायाचित्रे", models.Gallery.objects.count()),
        ("एकूण कार्यक्रम", models.EventMaster.objects.count()),
    ]
    recent = models.Registration.objects.order_by("-id")[:5]
    return render(request, "platform/dashboard.html", {
        "total_registrations": total_registrations,
        "total_subdomains": total_subdomains,
        "template_counts": template_counts,
        "site_summary": site_summary,
        "recent": recent,
    })
