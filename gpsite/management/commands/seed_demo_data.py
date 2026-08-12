from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from gpsite import models

DEMO_GPS = [
    {
        "gram_panchayat_name": "Padegaon Gram Panchayat",
        "taluka": "Karad",
        "district": "Satara",
        "template": "Template1",
        "population": 4200,
        "establish_year": "1962",
        "subdomain": "padegaon.digitalgp.in",
    },
    {
        "gram_panchayat_name": "Vadkhal Gram Panchayat",
        "taluka": "Panvel",
        "district": "Raigad",
        "template": "Template2",
        "population": 6100,
        "establish_year": "1958",
        "subdomain": "vadkhal.digitalgp.in",
    },
    {
        "gram_panchayat_name": "Wasantpuri Gram Panchayat",
        "taluka": "Shirur",
        "district": "Pune",
        "template": "Template3",
        "population": 3050,
        "establish_year": "1975",
        "subdomain": "wasantpuri.digitalgp.in",
    },
]

# Placeholder photos (picsum.photos -- free, no-auth public placeholder image CDN)
# so the sample content pages have something to render instead of blank boxes.
IMG = "https://picsum.photos/seed/{seed}/480/320"


class Command(BaseCommand):
    help = "Creates demo Gram Panchayat tenants + sample content for local multi-tenant testing."

    def handle(self, *args, **options):
        for entry in DEMO_GPS:
            entry = dict(entry)
            subdomain = entry.pop("subdomain")
            registration, created = models.Registration.objects.get_or_create(
                gram_panchayat_name=entry["gram_panchayat_name"],
                defaults=entry,
            )
            models.SubdomainDetail.objects.get_or_create(
                subdomain=subdomain,
                defaults={"register": registration},
            )
            status = "created" if created else "already existed"
            self.stdout.write(self.style.SUCCESS(
                f"{registration.gram_panchayat_name} ({subdomain}) — {status}"
            ))

        padegaon = models.Registration.objects.get(gram_panchayat_name="Padegaon Gram Panchayat")
        self._seed_content(padegaon)
        self.stdout.write(self.style.SUCCESS("Sample content seeded for Padegaon."))

        self._seed_admin_user(padegaon)

    def _seed_admin_user(self, gp):
        user, created = User.objects.get_or_create(
            username="padegaon_admin",
            defaults={"is_staff": True},
        )
        if created:
            user.set_password("padegaon@123")
            user.is_staff = True
            user.save()
        models.UserInfo.objects.get_or_create(
            user=user, defaults={"register": gp, "role": models.UserInfo.ROLE_ADMIN},
        )
        self.stdout.write(self.style.SUCCESS(
            "Demo GP-admin login -> username: padegaon_admin / password: padegaon@123 (Padegaon only)"
        ))

    def _seed_content(self, gp):
        about, _ = models.AboutUs.objects.get_or_create(
            register=gp,
            defaults={
                "description": "पडेगाव ही सातारा जिल्ह्यातील कराड तालुक्यातील एक प्रगतीशील ग्रामपंचायत आहे.",
                "nearest_railway_station": "कराड",
                "nearest_city": "कराड",
            },
        )
        for i in range(1, 4):
            models.AboutUsDetail.objects.get_or_create(
                about_us=about, image_name=f"village{i}.jpg",
                defaults={"image_url": IMG.format(seed=f"village{i}")},
            )

        models.History.objects.get_or_create(
            register=gp, history_desc="गावाची स्थापना १९६२ साली झाली.",
            defaults={"image_url": IMG.format(seed="history1")},
        )

        models.OtherHistory.objects.get_or_create(
            register=gp, title="ग्रामदैवत मंदिर इतिहास",
            defaults={"description": "गावातील प्राचीन मंदिराची १५० वर्षांहून जुनी परंपरा.", "image_url": IMG.format(seed="otherhist1")},
        )

        models.Suvichar.objects.get_or_create(
            register=gp, suvichar="स्वच्छ गाव, समृद्ध गाव — स्वच्छतेतून प्रगतीकडे.",
        )

        models.Announcement.objects.get_or_create(
            register=gp, title="ग्रामसभा सूचना",
            defaults={
                "description": "पुढील ग्रामसभा दिनांक १५ ऑगस्ट रोजी सकाळी १० वाजता आयोजित करण्यात आली आहे.",
                "importance": True, "image_url": IMG.format(seed="announce1"),
            },
        )

        img_type, _ = models.ImageTypeMaster.objects.get_or_create(
            register=gp, image_type_name="गाव दृश्य",
        )
        for i in range(1, 5):
            models.Gallery.objects.get_or_create(
                register=gp, image_title=f"गाव फोटो {i}", image_type=img_type,
                defaults={"image_url": IMG.format(seed=f"gallery{i}")},
            )

        event, _ = models.EventMaster.objects.get_or_create(
            register=gp, event_name="स्वातंत्र्य दिन सोहळा",
            defaults={"event_desc": "ग्रामपंचायत कार्यालयात ध्वजारोहण कार्यक्रम."},
        )
        for i in range(1, 3):
            models.EventDetail.objects.get_or_create(
                event_master=event, image_name=f"event{i}.jpg",
                defaults={"image_url": IMG.format(seed=f"event{i}")},
            )

        award, _ = models.Award.objects.get_or_create(
            register=gp, award_name="स्वच्छ ग्राम पुरस्कार",
            defaults={"award_des": "जिल्हा परिषदेकडून स्वच्छतेसाठी सन्मानित.", "award_date": "2024"},
        )
        models.AwardDetail.objects.get_or_create(
            award=award, img_name="award1.jpg",
            defaults={"img_url": IMG.format(seed="award1")},
        )

        pos_category, _ = models.PositionCategoryMaster.objects.get_or_create(
            register=gp, position_category_name="निर्वाचित पदाधिकारी",
        )
        sarpanch_pos, _ = models.PositionMaster.objects.get_or_create(
            register=gp, position_category=pos_category, position_name="सरपंच",
        )
        models.GrampanchayatBody.objects.get_or_create(
            register=gp, name="श्रीमती सुनिता पाटील", position=sarpanch_pos,
            defaults={"image_url": IMG.format(seed="sarpanch")},
        )

        models.LeadershipMember.objects.get_or_create(
            register=gp, name="श्री. रमेश जाधव",
            defaults={"designation": "उपसरपंच", "image_url": IMG.format(seed="leader1")},
        )

        models.JamaKharchPatrak.objects.get_or_create(
            register=gp, jama_kharch_nav="आर्थिक वर्ष 2024-25",
            defaults={"jama_rakkam": 1250000, "kharch_rakkam": 980000, "shillak_rakkam": 270000},
        )

        models.MahitiAdhikar.objects.get_or_create(
            register=gp, browse_uri="माहिती अधिकार अर्ज नमुना",
        )

        models.YojnaDetail.objects.get_or_create(
            register=gp, yojana_name="प्रधानमंत्री आवास योजना",
            defaults={
                "description": "ग्रामीण भागातील गरजू कुटुंबांना घरकुल योजनेचा लाभ.",
                "website_link": "https://pmayg.nic.in/",
            },
        )

        models.TouristGallery.objects.get_or_create(
            register=gp, paryatan_name="कृष्णा नदी घाट",
            defaults={"description": "गावाजवळील प्रसिद्ध नदीघाट व मंदिर परिसर.", "image_url": IMG.format(seed="tourist1")},
        )

        cat, _ = models.CategoryMaster.objects.get_or_create(register=gp, category="क्रीडा")
        models.Gauravshalivyakti.objects.get_or_create(
            register=gp, name="कु. प्रिया शिंदे", category=cat,
            defaults={"description": "राज्यस्तरीय कबड्डी स्पर्धेत सुवर्णपदक.", "image_url": IMG.format(seed="notable1")},
        )

        models.VillageSchool.objects.get_or_create(
            register=gp, school_name="जिल्हा परिषद प्राथमिक शाळा, पडेगाव",
            defaults={
                "school_address": "मुख्य रस्ता, पडेगाव", "headmaster_name": "श्री. विलास कदम",
                "total_boys": 85, "total_girls": 78, "total_teachers": 6,
                "established_year": 1965, "management_type": "जिल्हा परिषद", "medium": "मराठी",
                "school_photo_url": IMG.format(seed="school1"),
            },
        )

        models.SwachhBharatMission.objects.get_or_create(
            register=gp, title="घनकचरा व्यवस्थापन प्रकल्प",
            defaults={"description": "गावात ओला-सुका कचरा वर्गीकरण मोहीम राबवली जात आहे.", "image_url": IMG.format(seed="swachh1")},
        )

        models.PanchayatRajMission.objects.get_or_create(
            register=gp, title="समृद्ध पंचायत राज अभियान",
            defaults={"description": "ग्रामपंचायतीच्या सक्षमीकरणासाठी राज्यस्तरीय अभियान.", "img": IMG.format(seed="praj1")},
        )

        models.VitaritDakhle.objects.get_or_create(
            register=gp,
            defaults={
                "janm_dakhale": 42, "mrutu_dakhale": 18, "vivah_dakhale": 25,
                "daridrya_reshe_khalil_dakhale": 60, "thak_baki_naslyache_dakhale": 33,
                "niradhar_yojna_dakhale": 12, "rahivashi_dakhale": 90,
            },
        )

        models.UpiDetailsMaster.objects.get_or_create(
            register=gp,
            defaults={
                "gharpatti_upi_id": "padegaongp@okhdfcbank",
                "gharpatti_account_holder_name": "Padegaon Gram Panchayat",
                "panipatti_upi_id": "padegaongp.water@okhdfcbank",
                "panipatti_account_holder_name": "Padegaon Gram Panchayat Water Fund",
            },
        )

        models.AllMemberHistory.objects.get_or_create(
            register=gp, name="श्री. दत्तात्रय मोरे", position=sarpanch_pos,
            defaults={"start_year": "2015", "end_year": "2020", "image_url": IMG.format(seed="member1")},
        )

        models.PrashaskiyAdhikari.objects.get_or_create(
            register=gp, adhikari_name="श्री. संजय पवार", position=sarpanch_pos,
            defaults={"mobile_no": "9822011223", "image_url": IMG.format(seed="officer1")},
        )

        models.PrashaskiyVibhagP.objects.get_or_create(
            register=gp, zpgat="कराड पूर्व",
            defaults={"ps_gan1": "पडेगाव गण अ", "ps_gan2": "पडेगाव गण ब"},
        )

        models.JababdariBhumika.objects.get_or_create(
            position=sarpanch_pos,
            defaults={"bhumika": "ग्रामपंचायतीचे प्रमुख", "jababdari": "ग्रामसभा आयोजन व निर्णय अंमलबजावणी"},
        )

        models.AptkalinContact.objects.get_or_create(
            register=gp, vibhag_name="प्राथमिक आरोग्य केंद्र",
            defaults={"mobile_no": "9834011223", "telephone_no": "02164-123456"},
        )

        gram_work, _ = models.GramVikasKame.objects.get_or_create(
            register=gp, work_name="अंतर्गत रस्ते काँक्रिटीकरण",
            defaults={"yojna_name": "१५ वा वित्त आयोग", "manjur_nidhi": 850000, "kharch_nidhi": 620000, "status": "प्रगतीपथावर"},
        )
        models.GramVikasKameDetail.objects.get_or_create(
            gram_vikas_kame=gram_work, image_name="work1.jpg",
            defaults={"image_url": IMG.format(seed="work1")},
        )

        models.Video.objects.get_or_create(
            register=gp, title="ग्रामपंचायत परिचय",
            defaults={"description": "पडेगाव ग्रामपंचायतीचा अल्प परिचय व्हिडिओ.",
                      "video_url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"},
        )

        models.ImageSlider.objects.get_or_create(
            register=gp, image_name="banner1.jpg",
            defaults={"image_url": IMG.format(seed="banner1"), "content_type": "image"},
        )

        # NOTE: VibhagiyaAyukta and ShasanNirnay have no RegisterId column in the
        # original schema (shared reference data across all tenants), so these
        # are created without a `register=` argument.
        models.VibhagiyaAyukta.objects.get_or_create(
            name="श्री. डॉ. दिलीप शिंदे", defaults={"vibhag": "पुणे विभाग", "padh": "विभागीय आयुक्त"},
        )
        models.ShasanNirnay.objects.get_or_create(
            shasan_nirnay_name="ग्रामपंचायत करवसुली सवलत योजना - शासन निर्णय",
        )
