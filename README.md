# Pray and Obey Ministries

Flask marketing site and grant application intake for Pray and Obey Ministries.

Built by Between Sundays Agency.

---

## Stack

| Layer | Choice |
|---|---|
| Framework | Flask 3.0.3 + Jinja2 |
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

If `RESEND_API_KEY` is absent, the app logs the application payload instead of sending. Nothing is lost during local development.

---

## Editing content

All copy lives in `app.py` as Python dictionaries and lists. Templates read from these, so content changes never require touching Jinja logic.

| Data structure | Controls |
|---|---|
| `SITE` | Name, tagline, meta description, email, social links |
| `NAV` | Header navigation items |
| `HERO` | Headline, body, buttons, floating cards |
| `MISSION` | Mission section copy, badge, two pillars |
| `FOCUS` | The seven funding focus areas |
| `PROCESS` | The four application steps |
| `CRITERIA` | What we look for, good to know before applying |
| `FAQS` | Accordion questions and answers |
| `CLOSING_CTA` | Bottom call to action |
| `FOOTER` | Footer link columns |
| `ORG_TYPES`, `FUNDING_TYPES`, `AMOUNT_RANGES` | Application form dropdowns |

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
