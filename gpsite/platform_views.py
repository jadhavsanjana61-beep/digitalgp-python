"""
Platform-level views: not tied to any single Gram Panchayat's subdomain.
Only the platform superuser (the one who provisions new villages) can reach
these -- a village-level GP admin never sees this, same separation as the
SuperuserOnlyModelAdmin tables in admin.py.
"""

import re
import secrets
import string

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render

from . import models
from .platform_forms import RegisterGpForm

is_superuser = user_passes_test(lambda u: u.is_superuser, login_url="/admin/login/")


def _generate_username(gram_panchayat_name):
    slug = re.sub(r"[^a-z0-9]+", "", gram_panchayat_name.lower())[:20] or "gp"
    username = slug
    n = 1
    while User.objects.filter(username=username).exists():
        n += 1
        username = f"{slug}{n}"
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
                taluka=data["taluka"],
                district=data["district"],
                contact_no=data["contact_no"],
                email=data["email"],
                template=data["template"],
                status=True,
            )
            models.SubdomainDetail.objects.create(
                register=registration, subdomain=data["subdomain"],
            )
            username = _generate_username(data["gram_panchayat_name"])
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
    return render(request, "platform/register_gp.html", {"form": form, "created": created})


@login_required(login_url="/admin/login/")
@is_superuser
def gp_list_view(request):
    registrations = models.Registration.objects.prefetch_related("subdomaindetail_set").order_by("-id")
    return render(request, "platform/gp_list.html", {"registrations": registrations})
