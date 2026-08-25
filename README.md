# Pray and Obey Ministries

Flask marketing site and grant application intake for Pray and Obey Ministries.

Built by Between Sundays Agency.

---

## Stack

| Layer | Choice |
|---|---|
| Framework | Flask 3.0.3 + Jinja2 |
| Database | SQLAlchemy 2.x, SQLite locally, Postgres in production |
| Auth | Flask-Login |
| Server | Gunicorn |
| Hosting | Render (auto-deploy from GitHub `main`) |
| Email | Resend HTTP API, port 443 |
| CSS | Hand-authored, custom token system, no framework |
| JS | Vanilla, no dependencies |

---

## Routes

| Route | Purpose |
|---|---|
| `/` | Landing page: Hero, At a Glance, Mission, What We Fund, How It Works, Criteria, FAQ, CTA |
| `/apply` | Grant application form |
| `/thank-you` | Post-submission confirmation |
| 404 | Branded error page |

---

## Local setup

```bash
cd ~/"coding files/pray-and-obey"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill in real values
python app.py             # http://127.0.0.1:5000
```

---

## Environment variables

Set these in the Render dashboard for production. Never commit `.env`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing. Long random string. |
| `RESEND_API_KEY` | Resend sending key. Use a sending-only key, not a full-access key. |
| `MAIL_FROM` | Verified sender, e.g. `Pray and Obey <apply@prayandobey.org>` |
| `MAIL_TO` | Where applications are delivered |
| `FORM_MIN_SECONDS` | Minimum seconds before a submission is accepted. Default 8. |
| `DATABASE_URL` | Supplied by Render. Leave blank locally to use SQLite. |
| `FLASK_ENV` | Set to `development` locally so session cookies work without HTTPS. |

If `RESEND_API_KEY` is absent, the app logs the application payload instead of sending. Nothing is lost during local development.

---

## Editing content

All copy lives in `app.py` as Python dictionaries and lists. Templates read from these, so content changes never require touching Jinja logic.

| Data structure | Controls |
|---|---|
| `SITE` | Name, tagline, meta description, email, social links |
| `NAV` | Header and mobile menu links |
| `HERO` | Headline, body, buttons, floating cards |
| `IMPACT` | Our Impact: four areas, impact statement, Micah 6:8 quotation, guided-by line |
| `MISSION` | Mission section copy, two pillars |
| `FOCUS` | The seven funding focus areas |
| `PROCESS` | The four application steps |
| `CRITERIA` | What we look for, good to know before applying |
| `FAQS` | Accordion questions and answers |
| `VERSES` | The three Scripture references. See below. |
| `CLOSING_CTA` | Bottom call to action |
| `ORG_TYPES` | Organization type options on the application |
| `PRIORITIES` | Priority checkboxes in section 2 of the application |
| `BIBLE_WILLINGNESS` | Bible distribution options |
| `ASSISTANCE_TYPES` | Assistance requested checkboxes |
| `ATTACHMENTS` | Required attachments checklist |
| `BUDGET_ROWS` | Number of blank budget lines (default 5) |
| `CERTIFICATION_TEXT` | Legal certification wording |
| `REQUIRED_FIELDS` | Which fields block submission when empty |

Adding a focus area automatically adds it to the application form checkboxes. The grid handles the orphan card in the last row on its own.

---

## Photography

Two photo slots are filled. Both images are cropped to a 4:4.2 portrait ratio to match the source files.

| Path | Slot | Current image |
|---|---|---|
| `static/img/hero.jpg` | Hero image card | Ministry team praying over a young girl |
| `static/img/mission.jpg` | Mission section | Group standing arm in arm in prayer |

To swap either image, drop a replacement at the same path and push. Crop to roughly 4:4.2 portrait (for example 1200 x 1260) before saving, or the CSS will center-crop it for you.

The Criteria section no longer uses a photo. It renders as a two-column text layout.

**Source resolution note.** Both supplied files are 800 x 1200. That renders acceptably at 1x but is soft on retina displays. Higher-resolution originals (1600px wide or more) would sharpen the hero noticeably. Drop them at the same paths when available.

---

## Logo assets

| File | Where it is used | Notes |
|---|---|---|
| `logo-nav.png` | Masthead, on white | Word-cloud lockup with Matthew 3:11. 900px export, displayed at 264px desktop and 214px mobile. |
| `logo-mark.png` | Favicon, thank-you page, 404, portal sign in | Flame and book mark only, from the clean lockup. Sized by height. |
| `logo-full.png` | Open Graph share image | Word-cloud lockup at 1200px |

Each source file's flat background was removed using distance-based alpha so anti-aliased edges feather rather than stair-step.

The masthead sits at 264px rather than the 200px used by the previous lockup. The surrounding words render at roughly 6px cap height at 200px, which is too small to read; 264px brings them to a legible size.

`logo-mark.png` is deliberately cut from the plain lockup, not the word-cloud version. Cropping the icon out of the word cloud would slice through "service", "jesus", "love", and "faith".

---

## Brand tokens

Defined in `static/css/styles.css` under `:root`.

| Token | Hex | Use |
|---|---|---|
| `--navy` | `#0D2D5C` | Headings, dark bands, primary structure |
| `--gold` | `#D4A017` | Rules, icon strokes, section markers. Text only on navy. |
| `--flame` | `#C8102E` | Accent word, eyebrows, primary buttons |
| `--white` | `#FFFFFF` | Page background, primary sections |
| `--tint` | `#F2F5FA` | Light blue surface, derived from navy. Alternating sections and card fills. |
| `--cream` | `#F7F2E6` | Retained in the palette for the logo lockup. No longer used as a page background. |

Section backgrounds are white or navy only. `--tint` provides separation between adjacent light sections without introducing a third color family. Card surfaces invert automatically: white cards on tinted sections, tinted cards on white sections.

Gold measures 2.13:1 against cream, which fails WCAG for text. It is used structurally on light backgrounds and as text only on navy, where it measures 5.71:1.

---

## The grant application

`/apply` mirrors the Simplified Grant Application PDF in three sections:

1. **Organization and request.** Legal name, EIN, contact, mailing address, organization type, mission, Gospel activity, amount requested, project dates, summary, who is served.
2. **Mission alignment and Bible distribution.** Priority checkboxes, strongest fit, activities and timeline, use of funds, Bible distribution willingness and plan, Scripture engagement, assistance requested.
3. **Outcomes, finances, and certification.** Expected results, sustainability, risks, a five-line grant budget with a live total, attachments checklist, certification checkbox, authorized representative, title, and typed signature.

Twenty-six fields are required. Submission is blocked with a single message listing every missing field by name.

### Attachments

The form does not accept file uploads. There is no object storage attached to this deployment, and routing financial documents through email attachments creates a retention problem. Applicants confirm which documents they have ready; the fund requests them by email once an application is under review.

To change this, you would need S3 or Render disk storage plus a virus-scanning step. Not recommended before there is volume that justifies it.

### Electronic signature

The signature field captures a typed full legal name alongside the certification checkbox, and the submission timestamp is recorded automatically. This is a standard electronic signature pattern and is generally enforceable under E-SIGN and UETA. It is not a substitute for legal review if the fund wants a stronger evidentiary record.

---

## Scripture

| Where | What appears |
|---|---|
| Our Impact | Micah 6:8 quoted in full, plus a guided-by line citing Matthew 22:37-40 and Matthew 6:33 |
| Mission | Matthew 22:37-40, reference only |
| What We Fund | Micah 6:8, reference only |
| Criteria | Matthew 6:33, reference only |

Bare references live in `VERSES`. The quoted verse and its guided-by line live in `IMPACT`.

### Licensing

Because Micah 6:8 is now quoted in full, Crossway's attribution requirement applies. `SCRIPTURE_NOTICE` renders directly beneath the quotation in the impact statement panel, since the site has no footer.

**Do not remove that notice while any verse text is quoted.** If the quotation is ever cut back to a bare reference, the notice can go with it, because references alone carry no licensing obligation.

Crossway's Standard Use Guidelines permit quoting the ESV in digital formats up to 500 verses without a formal license, provided the quotations do not exceed half of any one book or 25 percent of the work they appear in, and are not used in a commentary or biblical reference work. One verse is well inside that. Full terms: https://www.crossway.org/permissions/

---

## Form protection

Two layers, both server-side. No third-party captcha, no external requests, no user friction.

1. **Honeypot.** A hidden `website_url` field. Any submission that fills it is silently dropped and redirected to the thank-you page, so bots see a success response.
2. **Timing gate.** A hidden timestamp is set on page render. Submissions faster than `FORM_MIN_SECONDS` are dropped the same way.

Both are logged at INFO level so you can see the volume in Render logs.

---

## Deploying to Render

1. Push to GitHub `main`.
2. Create a new Web Service in Render, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add the environment variables above.
6. Add the custom domain and point DNS.

`render.yaml` is included if you prefer blueprint deploys.

---

## DNS

Only add or modify A and CNAME records pointing to Render. Do not touch MX, DKIM, or SPF records. Screenshot the DNS state before and after any change.

Resend also requires DKIM and SPF records on the sending domain. Add those from the Resend dashboard before the first send, and screenshot before and after.

---

## Accessibility

- Skip-to-content link
- Visible keyboard focus on all interactive elements
- `prefers-reduced-motion` respected, scroll reveals disabled
- Semantic landmarks, labeled form fields, ARIA state on the mobile menu toggle
- All text and background pairs tested for contrast

---

## Pre-launch checklist

- [ ] Higher-resolution originals swapped in for hero and mission
- [ ] Written photo release or license confirmed for both images
- [ ] `SECRET_KEY` set to a long random value in Render
- [ ] `RESEND_API_KEY` created as a sending-only key
- [ ] Sending domain verified in Resend, DKIM and SPF added
- [ ] Test application submitted end to end, email received
- [ ] `MAIL_TO` confirmed as the right inbox
- [ ] Social URLs in `SITE["socials"]` confirmed live
- [ ] Custom domain connected, HTTPS active
- [ ] Repo kept private
- [ ] Postgres instance provisioned on Render
- [ ] At least two portal accounts created, one per team member
- [ ] Portal login tested over HTTPS on the live domain
- [ ] Data retention decision made for stored applications
