from django import forms


class GpLoginForm(forms.Form):
    """
    Deliberately plain username/password fields (not Django's AuthenticationForm)
    so the error messages below can stay in Marathi and this can't be confused
    with the separate platform-superuser login at /admin/login/.
    """
    username = forms.CharField(label="युजरनेम")
    password = forms.CharField(label="पासवर्ड", widget=forms.PasswordInput)


class TicketForm(forms.Form):
    """Citizen complaint / query form -- maps to TblTicket."""
    name = forms.CharField(label="तुमचे नाव", max_length=200)
    mobile_number = forms.CharField(label="मोबाईल नंबर", max_length=15)
    reason = forms.CharField(label="विषय", max_length=200)
    message = forms.CharField(label="तक्रार / संदेश", widget=forms.Textarea)
    photo = forms.ImageField(label="फोटो जोडा (ऐच्छिक)", required=False)
