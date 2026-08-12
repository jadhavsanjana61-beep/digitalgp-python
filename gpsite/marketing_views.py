"""
The platform's own public marketing/landing site -- served at the base domain
(no tenant resolved), mirroring the original app's Pages/Index.razor: hero,
a gallery of the 3 templates with a live iframe preview, and a public
"Publish Site" self-service signup (the original had this exact modal/model
but its HandlePublishAsync was entirely commented out in production, i.e. it
never actually worked -- here it's wired up for real, since a signup button
that does nothing isn't something worth reproducing faithfully).
"""

import json
import re

from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from . import models
from .maharashtra_locations import MAHARASHTRA_DISTRICTS_TALUKAS
from .platform_views import _generate_password, _username_from_mobile

DISTRICTS_TALUKAS_JSON = json.dumps(MAHARASHTRA_DISTRICTS_TALUKAS)

TEMPLATE_GALLERY = [
    {
        "id": "Template1",
        "name": "Template No.1",
        "description": "A clean, modern template for showcasing your Gram Panchayat.",
        "subdomain": "padegaon.digitalgp.in",
        "preview_seed": "template1preview",
    },
    {
        "id": "Template2",
        "name": "Template No.2",
        "description": "Showcase your village's work and services with style.",
        "subdomain": "vadkhal.digitalgp.in",
        "preview_seed": "template2preview",
    },
    {
        "id": "Template3",
        "name": "Template No.3",
        "description": "A bold, modern look for your village's digital presence.",
        "subdomain": "wasantpuri.digitalgp.in",
        "preview_seed": "template3preview",
    },
]


def landing_view(request):
    """Public marketing homepage -- only reachable when no tenant subdomain resolved."""
    village_count = models.Registration.objects.count()
    return render(request, "marketing/landing.html", {
        "templates": TEMPLATE_GALLERY,
        "village_count": village_count,
        "districts_talukas": MAHARASHTRA_DISTRICTS_TALUKAS,
        "districts_talukas_json": DISTRICTS_TALUKAS_JSON,
    })


def publish_site_view(request):
    """
    Public self-service signup -- the working version of the original's
    "Configure Your New Site" modal. Fields are trimmed to exactly what's
    needed: district, taluka, GP name (English + Marathi), mobile number,
    template, subdomain -- no Registration Type/Gram ID/Employee fields,
    those were internal company-CRM bookkeeping this project has no use for.
    Anyone can create a new Gram Panchayat tenant here, no login required.
    """
    village_count = models.Registration.objects.count()
    if request.method != "POST":
        return redirect("landing")

    template_id = request.POST.get("template_id", "Template1")
    district = request.POST.get("district", "").strip()
    taluka = request.POST.get("taluka", "").strip()
    gram_name_en = request.POST.get("gram_panchayat_name_en", "").strip()
    gram_name = request.POST.get("gram_panchayat_name", "").strip()
    contact_no = request.POST.get("contact_no", "").strip()
    subdomain_part = request.POST.get("subdomain_part", "").strip().lower()

    errors = []
    if district not in MAHARASHTRA_DISTRICTS_TALUKAS:
        errors.append("योग्य जिल्हा निवडा.")
    elif taluka not in MAHARASHTRA_DISTRICTS_TALUKAS[district]:
        errors.append("निवडलेल्या जिल्ह्यासाठी योग्य तालुका निवडा.")
    if not gram_name_en:
        errors.append("Gram Panchayat Name (English) आवश्यक आहे.")
    if not gram_name:
        errors.append("ग्रामपंचायतीचे नाव (मराठी) आवश्यक आहे.")
    if not re.match(r"^\+?[0-9]{10,15}$", contact_no):
        errors.append("मोबाईल क्रमांक 10-15 अंकी असावा.")
    if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$", subdomain_part):
        errors.append("Website address मध्ये फक्त letters, numbers, hyphens चालतील.")

    full_subdomain = f"{subdomain_part}.digitalgp.in"
    if not errors and models.SubdomainDetail.objects.filter(subdomain=full_subdomain).exists():
        errors.append("हा website address आधीच वापरात आहे, दुसरा निवडा.")
    if not errors and models.Registration.objects.filter(contact_no=contact_no).exists():
        errors.append("या संपर्क क्रमांकाने आधीच नोंदणी झाली आहे.")

    if errors:
        return render(request, "marketing/landing.html", {
            "templates": TEMPLATE_GALLERY, "village_count": village_count,
            "districts_talukas": MAHARASHTRA_DISTRICTS_TALUKAS,
            "districts_talukas_json": DISTRICTS_TALUKAS_JSON,
            "publish_errors": errors, "reopen_template_id": template_id,
        })

    registration = models.Registration.objects.create(
        gram_panchayat_name=gram_name, gram_panchayat_name_en=gram_name_en,
        district=district, taluka=taluka, contact_no=contact_no,
        template=template_id, status=True,
    )
    models.SubdomainDetail.objects.create(register=registration, subdomain=full_subdomain)
    username = _username_from_mobile(contact_no)
    password = _generate_password()
    user = User.objects.create_user(username=username, password=password, is_staff=True)
    models.UserInfo.objects.create(user=user, register=registration, role=models.UserInfo.ROLE_ADMIN)

    return render(request, "marketing/landing.html", {
        "templates": TEMPLATE_GALLERY, "village_count": village_count + 1,
        "districts_talukas": MAHARASHTRA_DISTRICTS_TALUKAS,
        "districts_talukas_json": DISTRICTS_TALUKAS_JSON,
        "published": {
            "gp": registration, "subdomain": full_subdomain,
            "username": username, "password": password,
        },
    })
