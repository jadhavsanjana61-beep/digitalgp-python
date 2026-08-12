"""
Django models for the GP (Gram Panchayat) website platform.

This is a fresh rewrite of the SQL Server / EF Core schema used by the legacy
Blazor app (Template2) onto PostgreSQL via Django. Field and model names have
been converted to idiomatic snake_case / PascalCase Django conventions and do
NOT mirror the original SQL Server column/table names 1:1 -- see the trailing
comment on each model for the original EF Core entity class and DB table name
for traceability back to `GpWebsiteTemplateContext.cs`.

Source of truth: Template2/Models/GpWebsiteTemplateContext.cs (OnModelCreating)
and the corresponding Template2/Models/Tbl*.cs entity classes.
"""

from django.db import models


# =====================================================================
# Abstract base classes
# =====================================================================

class TenantAuditModel(models.Model):
    """
    Shared shape for the large majority of tables: a `RegisterId` FK scoping
    the row to a single Gram Panchayat "tenant" (TblRegistration), plus the
    CreatedBy/CreatedOn/UpdatedBy/UpdatedOn audit columns that appear on
    almost every table in the original schema.

    NOTE: CreatedBy/UpdatedBy are plain integer user-id references in the
    original schema (never configured as real EF navigation FKs to
    TblUserInfo), so they stay as plain IntegerFields here rather than
    ForeignKeys.
    """
    register = models.ForeignKey(
        'Registration',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='%(class)s_set',
    )
    created_by = models.IntegerField(null=True, blank=True)
    created_on = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class AuditModel(models.Model):
    """
    Audit-only base for the handful of tables confirmed to have NO RegisterId
    column at all (TblShasanNirnay, TblVibhagiyaayuktum, TblJababdaribhumika)
    but that do still carry the CreatedBy/CreatedOn/UpdatedBy/UpdatedOn
    columns.
    """
    created_by = models.IntegerField(null=True, blank=True)
    created_on = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


# =====================================================================
# Multi-tenant core
# =====================================================================

class Registration(AuditModel):
    """maps to TblRegistration (table: TblRegistration) -- the multi-tenant root; one row = one Gram Panchayat."""
    gram_panchayat_name = models.TextField(blank=True, null=True)  # Marathi display name -- shown everywhere on the public site
    gram_panchayat_name_en = models.TextField(blank=True, null=True)  # English name -- registration/reference only
    taluka = models.TextField(blank=True, null=True)
    district = models.TextField(blank=True, null=True)
    gid = models.IntegerField(blank=True, null=True)  # column name override: GId
    email = models.TextField(blank=True, null=True)
    contact_no = models.CharField(max_length=15, blank=True, null=True)
    pin_code = models.CharField(max_length=50, blank=True, null=True)
    instagram = models.TextField(blank=True, null=True)
    facebook = models.TextField(blank=True, null=True)
    population = models.IntegerField(blank=True, null=True)
    area = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    gram_logo = models.TextField(blank=True, null=True)
    establish_year = models.CharField(max_length=10, blank=True, null=True)
    template = models.TextField(blank=True, null=True)
    emp_id = models.IntegerField(blank=True, null=True)
    emp_name = models.TextField(blank=True, null=True)
    publish_by_id = models.IntegerField(blank=True, null=True)
    publish_by_name = models.TextField(blank=True, null=True)
    status = models.BooleanField(blank=True, null=True)
    nagarik_portal_status = models.BooleanField(blank=True, null=True)
    migration_status = models.BooleanField(blank=True, null=True)
    start_stop_website_status = models.BooleanField(blank=True, null=True)
    registration_type = models.TextField(blank=True, null=True)
    property_count = models.IntegerField(blank=True, null=True)
    total_voter_count = models.IntegerField(blank=True, null=True)
    male_voter_count = models.IntegerField(blank=True, null=True)
    female_voter_count = models.IntegerField(blank=True, null=True)
    ward_count = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.gram_panchayat_name or f"Registration #{self.id}"


class UserInfo(TenantAuditModel):
    """
    maps to TblUserInfo (table: TblUserInfo) -- login profile for one Gram
    Panchayat's admin account.

    SECURITY FIX vs the original schema: the source table stored `UserName`/
    `Password` as plain columns with the password compared in cleartext (no
    hashing) in the legacy app's login page. Here, credentials are handled
    entirely by Django's built-in auth system (PBKDF2-hashed passwords,
    proper session management) via a one-to-one link to auth.User; this model
    only carries the GP-specific role + tenant.
    """
    ROLE_ADMIN = "Admin"
    ROLE_USER = "User"
    ROLE_CHOICES = [(ROLE_ADMIN, "Admin"), (ROLE_USER, "User")]

    user = models.OneToOneField(
        'auth.User', on_delete=models.CASCADE, related_name='gp_profile',
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default=ROLE_ADMIN)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class SubdomainDetail(TenantAuditModel):
    """maps to TblSubdomainDetail (table: TblSubdomainDetails, default EF table name)."""
    subdomain = models.TextField(blank=True, null=True)
    subdomain_id = models.IntegerField(blank=True, null=True)
    subdomain_guid = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.subdomain or f"SubdomainDetail #{self.id}"


class WebsiteStartStopDetail(models.Model):
    """
    maps to TblWebsiteStartStopDetail (table: TblWebsiteStartStopDetails, default EF table name).
    NOTE: source has a RegisterId column + Register navigation but NO audit
    columns at all -- does not use TenantAuditModel since that mixin would
    add created_by/created_on/updated_by/updated_on fields that don't exist
    on this table.
    """
    register = models.ForeignKey(
        'Registration', on_delete=models.CASCADE, null=True, blank=True,
        related_name='website_start_stop_details',
    )
    website_start_date = models.DateTimeField(blank=True, null=True)
    website_stop_date = models.DateTimeField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    current_status = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.current_status or f"WebsiteStartStopDetail #{self.id}"


# =====================================================================
# Lookup / master tables
# =====================================================================

class PositionCategoryMaster(TenantAuditModel):
    """maps to TblPositionCategoryMaster (table: TblPositionCategoryMaster)."""
    position_category_name = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.position_category_name or f"PositionCategoryMaster #{self.id}"


class PositionMaster(TenantAuditModel):
    """maps to TblPositionMaster (table: TblPositionMaster)."""
    position_category = models.ForeignKey(
        'PositionCategoryMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='positions',
    )
    position_name = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.position_name or f"PositionMaster #{self.id}"


class CategoryMaster(TenantAuditModel):
    """maps to TblCategoryMaster (table: TblCategoryMaster)."""
    category = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.category or f"CategoryMaster #{self.id}"


class ImageTypeMaster(TenantAuditModel):
    """maps to TblImageTypeMaster (table: TblImageTypeMaster)."""
    image_type_name = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image_type_name or f"ImageTypeMaster #{self.id}"


# =====================================================================
# CMS content
# =====================================================================

class AboutUs(TenantAuditModel):
    """maps to TblAboutU (table: TblAboutUs, default EF table name)."""
    description = models.TextField(blank=True, null=True)
    nearest_railway_station = models.TextField(blank=True, null=True)
    nearest_airport = models.TextField(blank=True, null=True)
    nearest_city = models.TextField(blank=True, null=True)
    location_accessibility = models.TextField(blank=True, null=True)
    map = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"About Us #{self.id}"


class AboutUsDetail(models.Model):
    """maps to TblAboutUsDetail (table: TblAboutUsDetails, default EF table name) -- image gallery rows for AboutUs. No RegisterId/audit columns in source."""
    about_us = models.ForeignKey(
        'AboutUs', on_delete=models.CASCADE, null=True, blank=True,
        related_name='details',
    )
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image_name or f"AboutUsDetail #{self.id}"


class Announcement(TenantAuditModel):
    """maps to TblAnnouncement (table: TblAnnouncement)."""
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    importance = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return self.title or f"Announcement #{self.id}"


class History(TenantAuditModel):
    """maps to TblHistory (table: TblHistory)."""
    history_desc = models.TextField(blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.history_desc or f"History #{self.id}"


class OtherHistory(TenantAuditModel):
    """maps to TblOtherHistory (table: TblOtherHistory)."""
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title or f"OtherHistory #{self.id}"


class Suvichar(TenantAuditModel):
    """maps to TblSuvichar (table: TblSuvichar) -- daily quote/thought."""
    suvichar = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.suvichar or f"Suvichar #{self.id}"


class ImageSlider(TenantAuditModel):
    """maps to TblImageSlider (table: TblImageSlider)."""
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    video_name = models.TextField(blank=True, null=True)
    video_url = models.TextField(blank=True, null=True)
    content_type = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image_name or self.video_name or f"ImageSlider #{self.id}"


class Video(TenantAuditModel):
    """maps to TblVideo (table: TblVideos, default EF table name)."""
    video_name = models.TextField(blank=True, null=True)
    video_url = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title or f"Video #{self.id}"


# =====================================================================
# Gallery
# =====================================================================

class Gallery(TenantAuditModel):
    """maps to TblGallery (table: TblGallery)."""
    image_type = models.ForeignKey(
        'ImageTypeMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='gallery_items',
    )
    image_title = models.TextField(blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image_title or f"Gallery #{self.id}"


class TouristGallery(TenantAuditModel):
    """maps to TblTouristGallery (table: TblTouristGallery)."""
    paryatan_name = models.TextField(blank=True, null=True)
    image_type = models.ForeignKey(
        'ImageTypeMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='tourist_gallery_items',
    )
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.paryatan_name or f"TouristGallery #{self.id}"


# =====================================================================
# Events / Awards
# =====================================================================

class EventMaster(TenantAuditModel):
    """maps to TblEventMaster (table: TblEventMaster)."""
    event_name = models.TextField(blank=True, null=True)
    event_desc = models.TextField(blank=True, null=True)
    event_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.event_name or f"EventMaster #{self.id}"


class EventDetail(models.Model):
    """maps to TblEventDetail (table: TblEventDetails, default EF table name) -- image gallery rows for EventMaster. No RegisterId/audit columns in source."""
    event_master = models.ForeignKey(
        'EventMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='details',
    )
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image_name or f"EventDetail #{self.id}"


class Award(TenantAuditModel):
    """maps to TblAward (table: TblAward)."""
    award_name = models.TextField(blank=True, null=True)
    award_des = models.TextField(blank=True, null=True)
    award_date = models.TextField(blank=True, null=True)  # C# type is string, not DateTime

    def __str__(self):
        return self.award_name or f"Award #{self.id}"


class AwardDetail(models.Model):
    """maps to TblAwardDetail (table: TblAwardDetail) -- image gallery rows for Award. No RegisterId/audit columns in source."""
    award = models.ForeignKey(
        'Award', on_delete=models.CASCADE, null=True, blank=True,
        related_name='details',
    )
    img_name = models.TextField(blank=True, null=True)
    img_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.img_name or f"AwardDetail #{self.id}"


class Gauravshalivyakti(TenantAuditModel):
    """maps to TblGauravshalivyakti (table: TblGauravshalivyakti) -- honoured/notable persons."""
    name = models.TextField(blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        'CategoryMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='gauravshalivyaktis',
    )  # C#: CatageryId / Catagery (original typo)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or f"Gauravshalivyakti #{self.id}"


# =====================================================================
# Officials / members
# =====================================================================

class GrampanchayatBody(TenantAuditModel):
    """maps to TblGrampanchyatBody (table: TblGrampanchyatBody)."""
    name = models.TextField(blank=True, null=True)
    position = models.ForeignKey(
        'PositionMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='grampanchayat_body_members',
    )
    contact_no = models.CharField(max_length=15, blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name or f"GrampanchayatBody #{self.id}"


class AllMemberHistory(TenantAuditModel):
    """maps to TblAllMemberHistory (table: TblAllMemberHistory) -- historical roster of body members."""
    name = models.TextField(blank=True, null=True)
    start_year = models.CharField(max_length=50, blank=True, null=True)
    end_year = models.CharField(max_length=50, blank=True, null=True)
    position = models.ForeignKey(
        'PositionMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='all_member_histories',
    )
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or f"AllMemberHistory #{self.id}"


class LeadershipMember(TenantAuditModel):
    """maps to TblLeadershipMember (table: tblLeadershipMembers -- note lowercase-leading table name in source DB)."""
    name = models.TextField(blank=True, null=True)
    designation = models.TextField(blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    matardarsang = models.TextField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name or f"LeadershipMember #{self.id}"


class PrashaskiyAdhikari(TenantAuditModel):
    """maps to TblPrashaskiyAdhikari (table: TblPrashaskiyAdhikari) -- administrative officers."""
    adhikari_name = models.TextField(blank=True, null=True)
    position = models.ForeignKey(
        'PositionMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='prashaskiy_adhikaris',
    )
    matdar_sangh = models.TextField(blank=True, null=True)
    mobile_no = models.TextField(blank=True, null=True)
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    tele_phone_no = models.TextField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.adhikari_name or f"PrashaskiyAdhikari #{self.id}"


class PrashaskiyVibhagP(TenantAuditModel):
    """
    maps to TblPrashaskiyVibhagP (table: TblPrashaskiyVibhagPs, default EF table name).
    NOTE: source FK column is named RegistrationId (not RegisterId) but still
    points at TblRegistration -- treated as the tenant FK here (`register`).
    """
    zpgat = models.CharField(max_length=250, blank=True, null=True)
    ps_gan1 = models.CharField(max_length=250, blank=True, null=True)
    ps_gan2 = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.zpgat or f"PrashaskiyVibhagP #{self.id}"


class JababdariBhumika(AuditModel):
    """maps to TblJababdaribhumika (table: TblJababdaribhumika) -- role/responsibility text per position. Confirmed NO RegisterId column in source."""
    position = models.ForeignKey(
        'PositionMaster', on_delete=models.CASCADE, null=True, blank=True,
        related_name='jababdari_bhumikas',
    )
    bhumika = models.TextField(blank=True, null=True)
    jababdari = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.bhumika or f"JababdariBhumika #{self.id}"


class VibhagiyaAyukta(AuditModel):
    """maps to TblVibhagiyaayuktum (table: TblVibhagiyaayukta, default EF table name; DbSet name TblVibhagiyaayukta). Confirmed NO RegisterId column in source."""
    name = models.TextField(blank=True, null=True)
    vibhag = models.TextField(blank=True, null=True)
    img = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    padh = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or f"VibhagiyaAyukta #{self.id}"


class AptkalinContact(TenantAuditModel):
    """maps to TblAptkalinContact (table: TblAptkalinContacts, default EF table name) -- emergency contacts."""
    vibhag_name = models.TextField(blank=True, null=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    telephone_no = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.vibhag_name or f"AptkalinContact #{self.id}"


# =====================================================================
# Finance
# =====================================================================

class JamaKharchPatrak(TenantAuditModel):
    """maps to TblJamaKharchPatrak (table: TblJamaKharchPatrak) -- income/expenditure statement."""
    jama_kharch_nav = models.TextField(blank=True, null=True)
    jama_rakkam = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    kharch_rakkam = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    shillak_rakkam = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    pdf_name = models.TextField(blank=True, null=True)  # column name override: PDFName
    pdf_url = models.TextField(blank=True, null=True)  # column name override: PDFURL

    def __str__(self):
        return self.jama_kharch_nav or f"JamaKharchPatrak #{self.id}"


class UpiDetailsMaster(TenantAuditModel):
    """
    maps to TblUpidetailsMaster (table: tblUPIDetailsMaster).
    NOTE: source has a RegisterId column but no Register navigation property
    and no HasOne(...) configured in OnModelCreating -- still treated as the
    tenant FK here since the column exists.
    """
    gharpatti_upi_id = models.TextField(blank=True, null=True)  # column name override: GharpattiUPIId
    gharpatti_account_holder_name = models.TextField(blank=True, null=True)
    panipatti_upi_id = models.TextField(blank=True, null=True)  # column name override: PanipattiUPIId
    panipatti_account_holder_name = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"UpiDetailsMaster #{self.id}"


# =====================================================================
# RTI / Government
# =====================================================================

class MahitiAdhikar(TenantAuditModel):
    """maps to TblMahitiAdhikar (table: TblMahitiAdhikar) -- Right to Information (RTI) documents."""
    browse_uri = models.TextField(blank=True, null=True)
    browse_image = models.TextField(blank=True, null=True)
    pdf_file = models.TextField(blank=True, null=True)  # column name override: PDFFile

    def __str__(self):
        return self.browse_uri or f"MahitiAdhikar #{self.id}"


class ShasanNirnay(AuditModel):
    """maps to TblShasanNirnay (table: TblShasanNirnay) -- government resolutions. Confirmed NO RegisterId column in source."""
    shasan_nirnay_name = models.TextField(blank=True, null=True)
    browse_uri = models.TextField(blank=True, null=True)
    browse_image = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.shasan_nirnay_name or f"ShasanNirnay #{self.id}"


class YojnaDetail(TenantAuditModel):
    """maps to TblYojnaDetail (table: TblYojnaDetails, default EF table name) -- government scheme details."""
    yojana_name = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    website_link = models.TextField(blank=True, null=True)
    logo_image_name = models.TextField(blank=True, null=True)
    logo_image_url = models.TextField(blank=True, null=True)
    browse_uri = models.TextField(blank=True, null=True)
    browse_pdf = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.yojana_name or f"YojnaDetail #{self.id}"


class GramVikasKame(models.Model):
    """
    maps to TblGramVikasKame (table: TblGramVikasKame) -- village development works.
    NOTE: source has a RegisterId column but NO audit columns at all -- does
    not use TenantAuditModel since that mixin would add created_by/created_on/
    updated_by/updated_on fields that don't exist on this table.
    """
    register = models.ForeignKey(
        'Registration', on_delete=models.CASCADE, null=True, blank=True,
        related_name='gram_vikas_kame_set',
    )
    yojna_name = models.TextField(blank=True, null=True)
    work_name = models.TextField(blank=True, null=True)
    manjur_nidhi = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    kharch_nidhi = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.work_name or f"GramVikasKame #{self.id}"


class GramVikasKameDetail(models.Model):
    """maps to TblGramVikasKameDetail (table: TblGramVikasKameDetails, default EF table name) -- image gallery rows for GramVikasKame. No RegisterId/audit columns in source."""
    gram_vikas_kame = models.ForeignKey(
        'GramVikasKame', on_delete=models.CASCADE, null=True, blank=True,
        related_name='details',
    )
    image_name = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image_name or f"GramVikasKameDetail #{self.id}"


class PanchayatRajMission(TenantAuditModel):
    """
    maps to TblPanchayatRajMission (table: TblPanchayatRajMission).
    NOTE: source has a RegisterId column but no Register navigation property
    and no HasOne(...) configured in OnModelCreating -- still treated as the
    tenant FK here since the column exists.
    """
    description = models.TextField(blank=True, null=True)
    img = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title or f"PanchayatRajMission #{self.id}"


class SwachhBharatMission(TenantAuditModel):
    """
    maps to TblSwachhBharatMission (table: TblSwachhBharatMission) -- Clean India Mission content.
    NOTE: source has a RegisterId column but no Register navigation property
    and no HasOne(...) configured in OnModelCreating -- still treated as the
    tenant FK here since the column exists.
    """
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    videos = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)  # column name override: ImageURL
    videos_url = models.TextField(blank=True, null=True)  # column name override: VideosURL
    documents = models.TextField(blank=True, null=True)
    scheme_type = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title or f"SwachhBharatMission #{self.id}"


class VitaritDakhle(TenantAuditModel):
    """
    maps to TblVitaritDakhle (table: TblVitaritDakhle) -- issued-certificates counters (birth/death/marriage/etc.).
    NOTE: source has a RegisterId column but no Register navigation property
    and no HasOne(...) configured in OnModelCreating -- still treated as the
    tenant FK here since the column exists.
    """
    janm_dakhale = models.IntegerField(blank=True, null=True)
    mrutu_dakhale = models.IntegerField(blank=True, null=True)
    vivah_dakhale = models.IntegerField(blank=True, null=True)
    daridrya_reshe_khalil_dakhale = models.IntegerField(blank=True, null=True)
    thak_baki_naslyache_dakhale = models.IntegerField(blank=True, null=True)
    niradhar_yojna_dakhale = models.IntegerField(blank=True, null=True)
    rahivashi_dakhale = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"VitaritDakhle #{self.id}"


# =====================================================================
# Citizen services
# =====================================================================

class Ticket(models.Model):
    """
    maps to TblTicket (table: TblTicket) -- citizen complaint/query tickets.
    NOTE: source has RegisterId and CreatedOn only -- no CreatedBy, UpdatedBy
    or UpdatedOn columns -- so this does not use TenantAuditModel.
    """
    register = models.ForeignKey(
        'Registration', on_delete=models.CASCADE, null=True, blank=True,
        related_name='tickets',
    )
    name = models.TextField(blank=True, null=True)
    mobile_number = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    takrar_img = models.TextField(blank=True, null=True)
    takrar_url = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or f"Ticket #{self.id}"


class VillageSchool(TenantAuditModel):
    """
    maps to TblVillageSchool (table: TblVillageSchools, default EF table name).
    NOTE: source has a RegisterId column but no Register navigation property
    and no HasOne(...) configured in OnModelCreating -- still treated as the
    tenant FK here since the column exists. SchoolName is IsRequired() in the
    source fluent config, so it is kept non-nullable/non-blank here.
    """
    school_name = models.TextField()
    school_address = models.TextField(blank=True, null=True)
    headmaster_name = models.TextField(blank=True, null=True)
    headmaster_photo_url = models.TextField(blank=True, null=True)
    headmaster_photo_name = models.TextField(blank=True, null=True)
    school_photo_url = models.TextField(blank=True, null=True)
    school_photo_name = models.TextField(blank=True, null=True)
    total_boys = models.IntegerField(default=0, blank=True, null=True)
    total_girls = models.IntegerField(default=0, blank=True, null=True)
    total_teachers = models.IntegerField(default=0, blank=True, null=True)
    contact_number = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    established_year = models.IntegerField(blank=True, null=True)
    management_type = models.TextField(blank=True, null=True)
    medium = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.school_name or f"VillageSchool #{self.id}"
