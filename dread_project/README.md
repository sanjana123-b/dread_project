# ThreatScope — DREAD Risk Analysis (Django)

A web application for performing **DREAD threat modeling** (Damage, Reproducibility,
Exploitability, Affected Users, Discoverability) on your systems/applications.

## Features

- User accounts (signup/login/logout) — each user's projects are private to them
- **Projects**: represent a system/app you're threat-modeling
- **Threats**: each rated 1–10 across all five DREAD categories
  - Auto-calculated **DREAD score** (average of the 5 ratings)
  - Auto-assigned **risk level**: Critical (≥8), High (≥6), Medium (≥4), Low (<4)
  - Optional STRIDE category tagging (Spoofing, Tampering, Repudiation, etc.)
  - Status tracking: Open / Mitigated / Risk Accepted / False Positive
  - Mitigation notes field
- Dashboard with aggregate stats, risk distribution bar, and top-5 highest-risk threats
- Per-project filtering by search term, status, and risk level
- **CSV export** of a project's full DREAD report
- Django admin panel for direct data management

## Project structure

```
dread_project/
├── manage.py
├── requirements.txt
├── dread_project/          # project settings/urls
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── analysis/                # the DREAD app
│   ├── models.py           # Project, Threat models + scoring logic
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── templates/analysis/      # all HTML templates
└── static/analysis/css/     # stylesheet
```

## Setup — run from scratch

1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply migrations** (creates the SQLite database)
   ```bash
   python manage.py migrate
   ```

4. **Create an admin/superuser** (optional, for /admin/ access)
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. Open **http://127.0.0.1:8000/** in your browser.
   - Sign up for a new account, or log in.
   - Create a Project, then add Threats and rate them on the 5 DREAD factors.
   - View the dashboard for an aggregate risk overview.
   - Export any project's threats to CSV from the project page.

## How DREAD scoring works (`analysis/models.py`)

Each threat stores five integers (1–10): `damage`, `reproducibility`,
`exploitability`, `affected_users`, `discoverability`.

```python
dread_score = (damage + reproducibility + exploitability + affected_users + discoverability) / 5
```

Risk level thresholds (customizable in `Threat.risk_level`):

| Score range | Level    |
|-------------|----------|
| 8.0 – 10.0  | Critical |
| 6.0 – 7.99  | High     |
| 4.0 – 5.99  | Medium   |
| 0.0 – 3.99  | Low      |

## Going to production

Before deploying, at minimum:

- Set `DEBUG = False` in `settings.py`
- Set `ALLOWED_HOSTS` to your actual domain(s) — it's currently `['*']` for local dev
- Set `SECRET_KEY` from an environment variable, not the hardcoded dev key
- Switch from SQLite to PostgreSQL for anything beyond a single-user demo
- Run `python manage.py collectstatic` and serve static files via your web server / whitenoise
- Put it behind HTTPS

## Extending it further

Ideas if you want to keep building on this for a course project or portfolio piece:

- Add a many-to-many "assets" or "attack surface" model per project
- PDF export of the DREAD report (the `pdf` skill / `reportlab`/`weasyprint` work well here)
- Role-based access so teams can collaborate on the same project
- Chart.js visualizations on the dashboard instead of the plain CSS bar
- REST API (Django REST Framework) so a frontend (React) could consume it
- Audit log of who changed a threat's rating and when
