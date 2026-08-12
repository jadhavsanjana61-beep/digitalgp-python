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
    Neither local dev nor the free Render deployment have real per-tenant DNS
    (local: no hosts-file edit, needs admin rights; Render free tier: only the
    one *.onrender.com host), so whenever the Host header itself doesn't match
    a real registered subdomain, a "?subdomain=..." query param / "dev_subdomain"
    session value is accepted as a fallback. This is intentionally NOT limited to
    DEBUG mode -- it only ever kicks in when the host didn't already resolve to a
    tenant, so it can't be used to override a real subdomain's own site.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        request.tenant = None
        request.tenant_template = None

        subdomain_key = None if host == settings.BASE_DOMAIN.lower() else host
        detail = self._lookup(subdomain_key) if subdomain_key else None

        if detail is None:
            override = request.GET.get("subdomain")
            if override:
                request.session["dev_subdomain"] = override
            dev_key = request.session.get("dev_subdomain")
            if dev_key:
                detail = self._lookup(dev_key)

        if detail and detail.register:
            request.tenant = detail.register
            request.tenant_template = template_folder_for(detail.register)

        return self.get_response(request)

    @staticmethod
    def _lookup(subdomain_key):
        return (
            SubdomainDetail.objects.select_related("register")
            .filter(subdomain=subdomain_key)
            .first()
        )
