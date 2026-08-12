from django import forms


class GpLoginForm(forms.Form):
    """
    Deliberately plain username/password fields (not Django's AuthenticationForm)
    so the error messages below can stay in Marathi and this can't be confused
    with the separate platform-superuser login at /admin/login/.
    """
    username = forms.CharField(label="युजरनेम", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="पासवर्ड", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class TicketForm(forms.Form):
    """Citizen complaint / query form -- maps to TblTicket."""
    name = forms.CharField(label="तुमचे नाव", max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    mobile_number = forms.CharField(label="मोबाईल नंबर", max_length=15, widget=forms.TextInput(attrs={"class": "form-control"}))
    reason = forms.CharField(label="विषय", max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    message = forms.CharField(label="तक्रार / संदेश", widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}))
    photo = forms.ImageField(label="फोटो जोडा (ऐच्छिक)", required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
