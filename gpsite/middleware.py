from django.conf import settings

from .models import Registration, SubdomainDetail

# Registration.template stores values like "Template1" / "Template2" / "Template3".
# We render templates from a lowercased folder of the same name; anything unrecognised
# falls back to template1 so a bad/blank value never 500s the site.
KNOWN_TEMPLATES = {"template1", "template2", "template3"}
DEFAULT_TEMPLATE = "template1"


def template_folder_for(registration):
    name = (registration.template or "").strip().lower()
    return name if name in KNOWN_TEMPLATES else DEFAULT_TEMPLATE


class TenantResolutionMiddleware:
    """
    Resolves which Gram Panchayat (tenant) the current request belongs to, replacing
    the original app's per-page host-lookup + hand-rolled Yarp forwarding with a single
    lookup done once per request.

    - request.tenant: the resolved Registration row, or None if this is the base
      domain / no matching subdomain was found.
    - request.tenant_template: "template1" / "template2" / "template3" (only set
      when request.tenant is set) -- which template folder to render.

    Real subdomains (e.g. padegaon.digitalgp.in) are resolved from the Host header.
    Since local dev has no real DNS and we're deliberately not touching Windows'
    hosts file (needs admin rights), DEBUG mode also accepts a "?subdomain=..."
    query param or a "dev_subdomain" session value so multi-tenant switching can be
    demoed without any DNS/hosts setup.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        subdomain_key = None

        if host != settings.BASE_DOMAIN.lower():
            subdomain_key = host

        if settings.DEBUG and host in ("localhost", "127.0.0.1"):
            override = request.GET.get("subdomain")
            if override:
                request.session["dev_subdomain"] = override
            subdomain_key = request.session.get("dev_subdomain")

        request.tenant = None
        request.tenant_template = None

        if subdomain_key:
            detail = (
                SubdomainDetail.objects.select_related("register")
                .filter(subdomain=subdomain_key)
                .first()
            )
            if detail and detail.register:
                request.tenant = detail.register
                request.tenant_template = template_folder_for(detail.register)

        return self.get_response(request)
