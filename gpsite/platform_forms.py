from django import forms

from . import models

TEMPLATE_CHOICES = [("Template1", "Template 1 (हरित)"), ("Template2", "Template 2 (भगवा)"), ("Template3", "Template 3 (डार्क)")]


class RegisterGpForm(forms.Form):
    """Platform-level onboarding form -- creates a new Gram Panchayat tenant
    in one step, mirroring the original app's GramPanchyatRegistration.razor
    (minus the Plesk/DNS provisioning call, which needs real hosting infra
    this project doesn't have)."""
    gram_panchayat_name = forms.CharField(label="ग्रामपंचायतीचे नाव", max_length=200)
    taluka = forms.CharField(label="तालुका", max_length=100)
    district = forms.CharField(label="जिल्हा", max_length=100)
    contact_no = forms.CharField(label="संपर्क क्रमांक", max_length=15)
    email = forms.EmailField(label="ईमेल", required=False)
    template = forms.ChoiceField(label="टेम्प्लेट", choices=TEMPLATE_CHOICES)
    subdomain = forms.CharField(
        label="सबडोमेन", max_length=200,
        help_text="उदा. newgaon.digitalgp.in",
    )

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
