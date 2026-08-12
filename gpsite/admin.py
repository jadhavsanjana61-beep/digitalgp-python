from django import forms
from django.contrib import admin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from . import models
from .media_utils import compress_video


class SuperuserOnlyModelAdmin(admin.ModelAdmin):
    """
    For platform-level tables (Registration, UserInfo, SubdomainDetail,
    WebsiteStartStopDetail) that a village-level Gram Panchayat admin should
    never see or touch -- only the platform superuser manages tenants.
    """
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class TenantScopedModelAdmin(admin.ModelAdmin):
    """
    Makes Django admin double as the per-village CMS backend: a logged-in Gram
    Panchayat admin (is_staff=True, is_superuser=False, with a UserInfo
    profile linking them to one Registration) only ever sees/edits rows
    belonging to their own village. The platform superuser is unrestricted.

    Tables without a `register` FK (shared reference data, or master/detail
    child rows whose parent already carries the tenant) are left unscoped --
    listed here for traceability rather than guessed at request time.
    """

    def _tenant_register(self, request):
        if request.user.is_superuser:
            return None  # None == "no restriction"
        profile = getattr(request.user, 'gp_profile', None)
        if profile is None or profile.register_id is None:
            return False  # False == "no access at all"
        return profile.register

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        register = self._tenant_register(request)
        if register is None or not hasattr(self.model, 'register_id'):
            return qs
        if register is False:
            return qs.none()
        return qs.filter(register=register)

    # Tenant staff accounts are plain is_staff users with no Django Permission
    # rows assigned (we don't manage a Permission/Group matrix for this
    # project) -- so access here is gated on is_staff directly rather than
    # Django's default has_perm(...) checks, with the real isolation enforced
    # by get_queryset (listing) and the object-level checks below (editing).
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if not (request.user.is_active and request.user.is_staff):
            return False
        if obj is None or request.user.is_superuser or not hasattr(obj, 'register_id'):
            return True
        register = self._tenant_register(request)
        return register is not False and obj.register_id == register.id

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        register = self._tenant_register(request)
        if not change and register not in (None, False) and hasattr(obj, 'register_id'):
            obj.register = register
        super().save_model(request, obj, form, change)


# ---- Multi-tenant core ----

@admin.register(models.Registration)
class RegistrationAdmin(SuperuserOnlyModelAdmin):
    list_display = ('id', 'gram_panchayat_name', 'taluka', 'district', 'status', 'created_on')
    search_fields = ('gram_panchayat_name', 'taluka', 'district')


@admin.register(models.UserInfo)
class UserInfoAdmin(SuperuserOnlyModelAdmin):
    list_display = ('id', 'user', 'role', 'register', 'created_on')
    list_filter = ('register', 'role')


@admin.register(models.SubdomainDetail)
class SubdomainDetailAdmin(SuperuserOnlyModelAdmin):
    list_display = ('id', 'subdomain', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.WebsiteStartStopDetail)
class WebsiteStartStopDetailAdmin(SuperuserOnlyModelAdmin):
    list_display = ('id', 'register', 'current_status', 'website_start_date', 'website_stop_date')
    list_filter = ('register', 'current_status')


# ---- Lookup / master tables ----

@admin.register(models.PositionCategoryMaster)
class PositionCategoryMasterAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'position_category_name', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.PositionMaster)
class PositionMasterAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'position_name', 'role', 'position_category', 'register')
    list_filter = ('register', 'position_category')


@admin.register(models.CategoryMaster)
class CategoryMasterAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'category', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.ImageTypeMaster)
class ImageTypeMasterAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'image_type_name', 'register', 'created_on')
    list_filter = ('register',)


# ---- CMS content ----

@admin.register(models.AboutUs)
class AboutUsAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'register', 'nearest_city', 'created_on')
    list_filter = ('register',)


@admin.register(models.AboutUsDetail)
class AboutUsDetailAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'about_us', 'image_name')


@admin.register(models.Announcement)
class AnnouncementAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'title', 'register', 'date', 'importance', 'created_on')
    list_filter = ('register', 'importance')
    search_fields = ('title', 'description')


@admin.register(models.History)
class HistoryAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.OtherHistory)
class OtherHistoryAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'title', 'register', 'created_on')
    list_filter = ('register',)
    search_fields = ('title',)


@admin.register(models.Suvichar)
class SuvicharAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'suvichar', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.ImageSlider)
class ImageSliderAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'image_name', 'content_type', 'register', 'created_on')
    list_filter = ('register', 'content_type')


class VideoAdminForm(forms.ModelForm):
    video_file = forms.FileField(
        required=False,
        help_text="Raw video upload -- compressed to 720p via ffmpeg on save (mirrors the "
                   "original app's VideoCompressionService). Leave blank to edit video_url by hand.",
    )

    class Meta:
        model = models.Video
        fields = '__all__'


@admin.register(models.Video)
class VideoAdmin(TenantScopedModelAdmin):
    form = VideoAdminForm
    list_display = ('id', 'title', 'register', 'created_on')
    list_filter = ('register',)
    search_fields = ('title', 'description')

    def save_model(self, request, obj, form, change):
        uploaded = form.cleaned_data.get('video_file')
        if uploaded:
            compressed = compress_video(uploaded, filename_hint=uploaded.name)
            file_to_save = compressed or ContentFile(uploaded.read(), name=uploaded.name)
            saved_path = default_storage.save(f"videos/{file_to_save.name}", file_to_save)
            obj.video_name = file_to_save.name
            obj.video_url = default_storage.url(saved_path)
        super().save_model(request, obj, form, change)


# ---- Gallery ----

@admin.register(models.Gallery)
class GalleryAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'image_title', 'image_type', 'register', 'created_on')
    list_filter = ('register', 'image_type')


@admin.register(models.TouristGallery)
class TouristGalleryAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'paryatan_name', 'image_type', 'register', 'created_on')
    list_filter = ('register', 'image_type')


# ---- Events / Awards ----

@admin.register(models.EventMaster)
class EventMasterAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'event_name', 'event_date', 'register', 'created_on')
    list_filter = ('register',)
    search_fields = ('event_name',)


@admin.register(models.EventDetail)
class EventDetailAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'event_master', 'image_name')


@admin.register(models.Award)
class AwardAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'award_name', 'award_date', 'register', 'created_on')
    list_filter = ('register',)
    search_fields = ('award_name',)


@admin.register(models.AwardDetail)
class AwardDetailAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'award', 'img_name')


@admin.register(models.Gauravshalivyakti)
class GauravshalivyaktiAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'name', 'category', 'register', 'created_on')
    list_filter = ('register', 'category')
    search_fields = ('name',)


# ---- Officials / members ----

@admin.register(models.GrampanchayatBody)
class GrampanchayatBodyAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'name', 'position', 'register', 'status')
    list_filter = ('register', 'position')
    search_fields = ('name',)


@admin.register(models.AllMemberHistory)
class AllMemberHistoryAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'name', 'position', 'start_year', 'end_year', 'register')
    list_filter = ('register', 'position')
    search_fields = ('name',)


@admin.register(models.LeadershipMember)
class LeadershipMemberAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'name', 'designation', 'register', 'status')
    list_filter = ('register',)
    search_fields = ('name', 'designation')


@admin.register(models.PrashaskiyAdhikari)
class PrashaskiyAdhikariAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'adhikari_name', 'position', 'register', 'status')
    list_filter = ('register', 'position')
    search_fields = ('adhikari_name',)


@admin.register(models.PrashaskiyVibhagP)
class PrashaskiyVibhagPAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'zpgat', 'ps_gan1', 'ps_gan2', 'register')
    list_filter = ('register',)


@admin.register(models.JababdariBhumika)
class JababdariBhumikaAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'position', 'bhumika', 'created_on')
    list_filter = ('position',)


@admin.register(models.VibhagiyaAyukta)
class VibhagiyaAyuktaAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'name', 'vibhag', 'created_on')
    search_fields = ('name', 'vibhag')


@admin.register(models.AptkalinContact)
class AptkalinContactAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'vibhag_name', 'mobile_no', 'telephone_no', 'register')
    list_filter = ('register',)


# ---- Finance ----

@admin.register(models.JamaKharchPatrak)
class JamaKharchPatrakAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'jama_kharch_nav', 'jama_rakkam', 'kharch_rakkam', 'shillak_rakkam', 'register')
    list_filter = ('register',)


@admin.register(models.UpiDetailsMaster)
class UpiDetailsMasterAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'gharpatti_account_holder_name', 'panipatti_account_holder_name', 'register', 'created_on')
    list_filter = ('register',)


# ---- RTI / Government ----

@admin.register(models.MahitiAdhikar)
class MahitiAdhikarAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'browse_uri', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.ShasanNirnay)
class ShasanNirnayAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'shasan_nirnay_name', 'created_on')
    search_fields = ('shasan_nirnay_name',)


@admin.register(models.YojnaDetail)
class YojnaDetailAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'yojana_name', 'register', 'created_on')
    list_filter = ('register',)
    search_fields = ('yojana_name',)


@admin.register(models.GramVikasKame)
class GramVikasKameAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'work_name', 'yojna_name', 'status', 'manjur_nidhi', 'kharch_nidhi', 'register')
    list_filter = ('register', 'status')
    search_fields = ('work_name', 'yojna_name')


@admin.register(models.GramVikasKameDetail)
class GramVikasKameDetailAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'gram_vikas_kame', 'image_name')


@admin.register(models.PanchayatRajMission)
class PanchayatRajMissionAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'title', 'register', 'created_on')
    list_filter = ('register',)


@admin.register(models.SwachhBharatMission)
class SwachhBharatMissionAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'title', 'scheme_type', 'register', 'created_on')
    list_filter = ('register', 'scheme_type')


@admin.register(models.VitaritDakhle)
class VitaritDakhleAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'register', 'janm_dakhale', 'mrutu_dakhale', 'vivah_dakhale', 'created_on')
    list_filter = ('register',)


# ---- Citizen services ----

@admin.register(models.Ticket)
class TicketAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'name', 'mobile_number', 'status', 'register', 'created_on')
    list_filter = ('register', 'status')
    search_fields = ('name', 'mobile_number')


@admin.register(models.VillageSchool)
class VillageSchoolAdmin(TenantScopedModelAdmin):
    list_display = ('id', 'school_name', 'headmaster_name', 'management_type', 'register')
    list_filter = ('register', 'management_type')
    search_fields = ('school_name', 'headmaster_name')
