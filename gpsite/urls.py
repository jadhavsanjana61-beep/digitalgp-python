from django.urls import path

from . import marketing_views, platform_views, views

urlpatterns = [
    path("platform/", platform_views.dashboard_view, name="platform_dashboard"),
    path("platform/register/", platform_views.register_gp_view, name="platform_register_gp"),
    path("platform/gram-panchayats/", platform_views.gp_list_view, name="platform_gp_list"),
    path("landing/", marketing_views.landing_view, name="landing"),
    path("publish-site/", marketing_views.publish_site_view, name="publish_site"),

    path("", views.home_view, name="home"),
    path("switch-tenant/", views.switch_tenant, name="switch_tenant"),

    path("about-us/", views.about_us_view, name="about_us"),
    path("history/", views.history_view, name="history"),
    path("announcements/", views.announcements_view, name="announcements"),
    path("gallery/", views.gallery_view, name="gallery"),

    path("events/", views.events_view, name="events"),
    path("events/<int:pk>/", views.event_detail_view, name="event_detail"),
    path("awards/", views.awards_view, name="awards"),
    path("awards/<int:pk>/", views.award_detail_view, name="award_detail"),

    path("grampanchayat-body/", views.grampanchayat_body_view, name="grampanchayat_body"),
    path("leadership/", views.leadership_view, name="leadership"),

    path("jama-kharch/", views.jama_kharch_view, name="jama_kharch"),
    path("mahiti-adhikar/", views.mahiti_adhikar_view, name="mahiti_adhikar"),
    path("yojana/", views.yojana_view, name="yojana"),

    path("tourist-gallery/", views.tourist_gallery_view, name="tourist_gallery"),
    path("gauravshalivyakti/", views.gauravshalivyakti_view, name="gauravshalivyakti"),
    path("village-schools/", views.village_schools_view, name="village_schools"),
    path("swachh-bharat-mission/", views.swachh_bharat_view, name="swachh_bharat"),
    path("panchayat-raj-mission/", views.panchayat_raj_mission_view, name="panchayat_raj_mission"),

    path("vitarit-dakhle/", views.vitarit_dakhle_view, name="vitarit_dakhle"),
    path("upi-details/", views.upi_details_view, name="upi_details"),
    path("takrar/", views.ticket_view, name="ticket"),

    path("member-history/", views.all_member_history_view, name="all_member_history"),
    path("prashaskiy-adhikari/", views.prashaskiy_adhikari_view, name="prashaskiy_adhikari"),
    path("prashaskiy-vibhag/", views.prashaskiy_vibhag_view, name="prashaskiy_vibhag"),
    path("jababdari-bhumika/", views.jababdari_bhumika_view, name="jababdari_bhumika"),
    path("vibhagiya-ayukta/", views.vibhagiya_ayukta_view, name="vibhagiya_ayukta"),
    path("aptkalin-contact/", views.aptkalin_contact_view, name="aptkalin_contact"),
    path("shasan-nirnay/", views.shasan_nirnay_view, name="shasan_nirnay"),
    path("gram-vikas-kame/", views.gram_vikas_kame_view, name="gram_vikas_kame"),
    path("gram-vikas-kame/<int:pk>/", views.gram_vikas_kame_detail_view, name="gram_vikas_kame_detail"),
    path("videos/", views.videos_view, name="videos"),
    path("other-history/", views.other_history_view, name="other_history"),

    path("login/", views.gp_login_view, name="gp_login"),
    path("logout/", views.gp_logout_view, name="gp_logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
]
