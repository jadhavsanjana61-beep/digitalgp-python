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
