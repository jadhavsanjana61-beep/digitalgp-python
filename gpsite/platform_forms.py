from django import forms

from . import models
from .maharashtra_locations import MAHARASHTRA_DISTRICTS_TALUKAS

TEMPLATE_CHOICES = [("Template1", "Template 1 (हरित)"), ("Template2", "Template 2 (भगवा)"), ("Template3", "Template 3 (डार्क)")]
DISTRICT_CHOICES = [(d, d) for d in sorted(MAHARASHTRA_DISTRICTS_TALUKAS)]


class RegisterGpForm(forms.Form):
    """
    Platform-level onboarding form -- creates a new Gram Panchayat tenant in
    one step, mirroring the original app's GramPanchyatRegistration.razor --
    trimmed down to exactly the fields actually needed (no Registration Type,
    Gram ID, Employee Name, or Published By -- those were internal
    company-CRM bookkeeping fields this project has no use for).
    """
    district = forms.ChoiceField(label="जिल्हा", choices=DISTRICT_CHOICES)
    taluka = forms.CharField(label="तालुका", max_length=100)
    gram_panchayat_name_en = forms.CharField(label="ग्रामपंचायतीचे नाव (इंग्रजी)", max_length=200)
    gram_panchayat_name = forms.CharField(label="ग्रामपंचायतीचे नाव (मराठी)", max_length=200)
    contact_no = forms.CharField(label="मोबाईल क्रमांक", max_length=15)
    template = forms.ChoiceField(label="टेम्प्लेट", choices=TEMPLATE_CHOICES)
    subdomain = forms.CharField(
        label="सबडोमेन", max_length=200,
        help_text="उदा. newgaon.digitalgp.in",
    )

    def clean_taluka(self):
        taluka = self.cleaned_data["taluka"].strip()
        district = self.data.get("district", "")
        valid_talukas = MAHARASHTRA_DISTRICTS_TALUKAS.get(district, [])
        if valid_talukas and taluka not in valid_talukas:
            raise forms.ValidationError("निवडलेल्या जिल्ह्यासाठी हा तालुका बरोबर नाही.")
        return taluka

    def clean_subdomain(self):
        subdomain = self.cleaned_data["subdomain"].strip().lower()
        if models.SubdomainDetail.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError("हा subdomain आधीच वापरात आहे.")
        return subdomain

    def clean_contact_no(self):
        contact_no = self.cleaned_data["contact_no"].strip()
        if models.Registration.objects.filter(contact_no=contact_no).exists():
            raise forms.ValidationError("या संपर्क क्रमांकाने आधीच नोंदणी झाली आहे.")
        return contact_no
