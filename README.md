# DigitalGp Python — Gram Panchayat Multi-Tenant Website Platform

मूळ .NET Blazor Server + SQL Server `DigitalGp`/`GPWebsiteTemplate` app चा हा Python (Django + PostgreSQL) मध्ये केलेला rewrite आहे. एका deployment मधून अनेक Gram Panchayat (गावं) आपापल्या subdomain वर आपापली website + admin CMS चालवू शकतात — पूर्णपणे मोफत/open-source stack वापरून.

---

## 1. काय बनवलं आहे (Feature Summary)

| भाग | स्थिती |
|---|---|
| Database schema (मूळ SQL Server च्या 43 tables वरून) | ✅ पूर्ण — Django models |
| Django Admin (आपोआप मिळणारा CRUD backend) | ✅ पूर्ण, प्रत्येक गावासाठी data वेगळं (tenant-scoped) |
| Multi-tenant subdomain resolution + Template1/2/3 theme switching | ✅ पूर्ण |
| 30 public पानं (About Us, History, Gallery, Events, Awards, Jama-Kharch, RTI, Yojana, इ.) | ✅ पूर्ण |
| सुरक्षित Login (hashed passwords, tenant-isolated) | ✅ पूर्ण |
| Image compression (अपलोड करताच आपोआप resize) | ✅ पूर्ण |
| Video compression (ffmpeg ने 720p पर्यंत आपोआप) | ✅ पूर्ण |
| नवीन Gram Panchayat नोंदणी (superuser साठी) | ✅ पूर्ण |
| UI polish (grouped nav menu, mobile-friendly, 3 themes) | ✅ पूर्ण |
| Deployment-ready (Render.com साठी) | ✅ ready, प्रत्यक्ष deploy करणं बाकी |

---

## 2. Tech Stack आणि का निवडलं

| भाग | निवड | का |
|---|---|---|
| Backend | **Django 6.1** (Python) | Built-in admin panel (जुन्या AdminDashboard सारखं काम फुकट करतो), ORM, hashed-password auth — सगळं framework मध्येच |
| Database | **PostgreSQL 17** | 100% मोफत, open-source, Django सोबत best काम करतं |
| Frontend | Django Templates + plain CSS (कुठलाही JS framework नाही) | साधं, एकाच भाषेत (Python), शिकायला सोपं |
| Image processing | **Pillow** | जुन्या SixLabors.ImageSharp ची जागा |
| Video processing | **ffmpeg** (binary, no installer) | जुन्या Xabe.FFmpeg ची जागा |
| QR codes | **qrcode** library | जुन्या QRCoder ची जागा |
| Editor | VS Code | मोफत, हलकं |

**मुद्दाम काय टाळलं:** SQL Server (paid-ish licensing), Azure Blob Storage (जुन्या कोडमध्ये त्याची key hardcoded सापडली होती — ती चूक होती, आपण टाळली), hardcoded admin backdoor (जुन्या `AutoLoginHandler.razor` मध्ये होता), plaintext passwords.

---

## 3. Project कुठे आहे आणि Folder Structure

```
D:\DigitalGpPython\                  ← मुख्य प्रोजेक्ट (हे संपूर्ण फोल्डर दुसऱ्या laptop वर कॉपी करायचं)
  ├── venv\                          ← Python virtual environment (कॉपी करू नकोस — नवीन laptop वर पुन्हा बनवायचं, खाली पद्धत आहे)
  ├── digitalgp_core\                ← Django प्रोजेक्ट सेटिंग्स (settings.py, urls.py)
  ├── gpsite\                        ← मुख्य app — इथेच जवळजवळ सगळा कोड आहे
  │     ├── models.py                ← 43 database tables (Django models)
  │     ├── admin.py                 ← Django admin मध्ये कुठलं table कसं दिसेल
  │     ├── views.py                 ← प्रत्येक पानामागचा logic (public pages, login, dashboard)
  │     ├── platform_views.py        ← नवीन गाव नोंदणी (superuser साठी)
  │     ├── urls.py                  ← कुठला URL कुठल्या view ला जातो
  │     ├── middleware.py            ← subdomain बघून कुठलं गाव आहे ते ठरवणारा भाग
  │     ├── media_utils.py           ← image/video compression
  │     ├── forms.py / platform_forms.py
  │     └── management/commands/seed_demo_data.py   ← डेमो डेटा भरणारी command
  ├── templates\
  │     ├── template1\ template2\ template3\   ← तीन themes (base.html — रंग/layout)
  │     ├── partials\                ← nav, footer, shared CSS (तिन्ही themes शेअर करतात)
  │     ├── content\                 ← प्रत्येक पानाचा actual content template
  │     └── platform\                ← superuser च्या "नवीन गाव नोंदणी" पानांचे templates
  ├── media\                         ← अपलोड केलेले फोटो/व्हिडिओ (गिट मध्ये नाही)
  ├── .env                           ← खरे secrets (गिट मध्ये कधीच नाही — .gitignore मध्ये आहे)
  ├── .env.example                   ← कुठले env variables लागतात त्याचा नमुना
  ├── requirements.txt               ← कुठले Python packages लागतात (नवीन laptop वर हेच वापरायचं)
  ├── manage.py                      ← Django चं मुख्य command-line tool
  ├── run_server.bat                 ← डबल-क्लिक करून database + website दोन्ही सुरू
  └── render.yaml                    ← Render.com वर deploy करण्यासाठी config
```

बाहेर (D drive वर, प्रोजेक्ट फोल्डरच्या बाहेर):
```
D:\DevTools\Python312\      ← Python इथे install आहे
D:\DevTools\PostgreSQL17\   ← Database इथे आहे (no-installer zip version)
D:\DevTools\ffmpeg\         ← Video compression साठी ffmpeg.exe इथे आहे
D:\DevTools\start_postgres.bat / stop_postgres.bat
```

---

## 4. Database कुठे असतो आणि त्याला कसं भेटायचं

- **Engine:** PostgreSQL 17, port 5432, लोकल कॉम्प्युटरवर चालतो (कुठलाही रिमोट सर्व्हर नाही)
- **Data प्रत्यक्ष कुठे साठतं:** `D:\DevTools\PostgreSQL17\data\` (हे फोल्डर = तुझा संपूर्ण डेटाबेस)
- **Database नाव:** `digitalgp_db`
- **Login:** user `postgres`, password `digitalgp123`
- **थेट डेटाबेस बघायचा असेल तर** (उदा. एखादी value चुकीची वाटली तर):
  ```bash
  D:\DevTools\PostgreSQL17\bin\psql.exe -U postgres -d digitalgp_db
  ```
  मग आत `\dt` टाकून सगळे tables दिसतील, किंवा `SELECT * FROM gpsite_registration;` सारखी query चालवता येईल.
- साधारणपणे थेट psql वापरायची गरज नाही — रोजचं काम **Django Admin** (`/admin/`) मधूनच होतं.

---

## 5. रोज काम सुरू करताना (आधीच सेटअप झालेल्या याच laptop वर)

1. डबल-क्लिक: **`D:\DigitalGpPython\run_server.bat`**
   (हे आधी database सुरू करतं, मग website सुरू करतं)
2. Browser मध्ये उघड: **http://localhost:8000**
3. वेगवेगळी गावं बघायला: `http://localhost:8000/?subdomain=padegaon.digitalgp.in` (किंवा `vadkhal.digitalgp.in`, `wasantpuri.digitalgp.in`)
4. Admin panel: **http://localhost:8000/admin/** — login: `admin` / `digitalgp123`
5. एका गावाचा admin dashboard बघायला: `/login/?subdomain=padegaon.digitalgp.in` — login: `padegaon_admin` / `padegaon@123`
6. बंद करताना: टर्मिनल विंडो बंद कर (`Ctrl+C` दाबून, मग विंडो बंद कर)

---

## 6. Changes कसे करायचे (रोजचं development)

### (अ) नवीन content page/module जोडायचं असेल
1. `gpsite/models.py` — table आधीच आहे का बघ (43 tables आधीच बनलेले आहेत)
2. `gpsite/views.py` मध्ये एक नवीन function जोड (existing उदाहरणं कॉपी करून बदल — उदा. `history_view` बघ)
3. `gpsite/urls.py` मध्ये त्या view साठी एक `path(...)` जोड
4. `templates/content/` मध्ये आधीच generic templates आहेत (`generic_list.html`, `gallery_detail.html`) — बहुतेक वेळा नवीन template लागणारच नाही
5. `templates/partials/_nav.html` मध्ये नवीन लिंक जोड (हवं असल्यास)
6. Test करायला: `run_server.bat` चालवून browser मध्ये बघ

### (ब) Database मध्ये नवीन column/table जोडायचं असेल
1. `gpsite/models.py` मध्ये बदल कर
2. टर्मिनल मध्ये (venv activate करून):
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
3. `gpsite/admin.py` मध्ये नवीन model register कर (Django admin मध्ये दिसण्यासाठी)

### (क) Design/रंग बदलायचे असतील
- `templates/template1/base.html` (किंवा 2/3) च्या वरच्या `<style>` भागात `--accent`, `--bg` वगैरे CSS variables आहेत — तेच बदल
- सगळ्या themes ला common असलेलं (spacing, card style, nav) `templates/partials/_shared_styles.html` मध्ये आहे

### टर्मिनल मधून काम करायचं असेल (venv activate करून):
```powershell
cd D:\DigitalGpPython
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

---

## 7. दुसऱ्या Laptop वर हे Project घ्यायचं असेल तर

### काय install करावं लागेल (सगळं मोफत):

| Software | कुठून | आकार |
|---|---|---|
| Python 3.12 | winget: `winget install --id Python.Python.3.12` किंवा [python.org](https://www.python.org/downloads/) | ~30MB |
| PostgreSQL 17 | [postgresql.org](https://www.postgresql.org/download/windows/) installer, किंवा no-installer zip version [enterprisedb.com](https://www.enterprisedb.com/download-postgresql-binaries) (admin rights लागत नाहीत) | ~110MB |
| ffmpeg (video compression साठी) | [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) → "essentials" build (zip, installer नाही) | ~110MB |
| VS Code | [code.visualstudio.com](https://code.visualstudio.com/) | ~90MB |
| Git | [git-scm.com](https://git-scm.com/) (project कॉपी/GitHub साठी) | ~50MB |

### पायऱ्या (step by step):

1. **Python, PostgreSQL, ffmpeg, VS Code, Git install कर** (वरच्या टेबलप्रमाणे — installer असतील तर पुढे पुढे क्लिक करून install कर)

2. **Project फोल्डर कॉपी कर** — `D:\DigitalGpPython` मधलं सगळं नवीन laptop वर न्या, **पण `venv\` फोल्डर सोडून द्या** (तो प्रत्येक कॉम्प्युटरवर वेगळा बनवावा लागतो — मोठा असतो आणि कॉपी करून चालत नाही)
   - सगळ्यात सोपा मार्ग: जर GitHub वर push केलं असेल (खाली बघ), तर `git clone` कर

3. **PostgreSQL मध्ये database बनव:**
   ```
   psql -U postgres
   CREATE DATABASE digitalgp_db;
   ```
   (पासवर्ड install करतानाच ठरवशील — तोच `.env` मध्ये टाकायचा)

4. **Virtual environment नवीन बनव:**
   ```powershell
   cd D:\DigitalGpPython
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. **`.env` फाईल बनव** — `.env.example` ची कॉपी करून `.env` नाव दे, आणि त्यातली database माहिती तुझ्या नवीन PostgreSQL password प्रमाणे बदल

6. **Database तयार कर:**
   ```
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py seed_demo_data    (डेमो गावं + sample content हवं असल्यास)
   ```

7. **चालव:**
   ```
   python manage.py runserver
   ```
   आणि `http://localhost:8000` उघड

---

## 8. Deployment (मोफत, college मध्ये दाखवायला Live URL)

### शिफारस: **Render.com** (मोफत, credit card लागत नाही)

**महत्त्वाचं आधी समजून घे:**
- Render च्या मोफत tier वर app 15 मिनिटं वापर नसेल तर झोपतं (sleep), परत उघडायला पहिली वेळ 30-50 सेकंद लागतात — हे normal आहे, बिघाड नाही
- मोफत Postgres database 90 दिवसांनी expire होतो, मग नवीन बनवावा लागतो — डेमोसाठी पुरेसं आहे
- Media (फोटो/व्हिडिओ) साठवण्याची जागा कायमस्वरूपी नाही (restart वर उडू शकते) — डेमो डेटासाठी ठीक आहे

**पायऱ्या (हे तुलाच करावं लागेल, मी account बनवू शकत नाही):**

1. **GitHub वर account बनव** (मोफत) आणि एक नवीन repository तयार कर
2. या project ला GitHub शी जोड:
   ```
   git remote add origin https://github.com/<तुझं-username>/<repo-नाव>.git
   git branch -M main
   git push -u origin main
   ```
3. **Render.com वर account बनव** (मोफत, GitHub नेच login करता येतं)
4. Render dashboard मध्ये: **New → Blueprint** → तुझा GitHub repo निवड → हे project मध्येच तयार असलेला `render.yaml` वाचून आपोआप website + database दोन्ही बनवेल
5. काही मिनिटांत तुला एक URL मिळेल: `https://digitalgp-python.onrender.com`
6. एकदा live झालं की, तिथे जाऊन `/admin/` वापरून `createsuperuser` सारखं manually करावं लागेल (Render च्या "Shell" tab मधून: `python manage.py createsuperuser` आणि `python manage.py seed_demo_data`)

हे झाल्यावर तो एकच URL कॉलेजमध्ये दाखवता येईल — त्याच्यावरच्या picker page वरून वेगवेगळी गावं (`?subdomain=...`) दाखवता येतील.

---

## 9. Login Credentials (डेमो डेटासाठी)

| कोण | Username | Password | कुठे |
|---|---|---|---|
| Platform Superuser | `admin` | `digitalgp123` | `/admin/` — सगळं दिसतं/बदलता येतं |
| Padegaon गावाचा Admin | `padegaon_admin` | `padegaon@123` | `/login/?subdomain=padegaon.digitalgp.in` — फक्त त्याच गावाचं |
| PostgreSQL | `postgres` | `digitalgp123` | थेट database access साठी |

**सूचना:** हे demo credentials आहेत — प्रत्यक्ष कुठेही public दाखवण्याआधी हे पासवर्ड बदल (`python manage.py changepassword admin`).
