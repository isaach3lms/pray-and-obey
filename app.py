"""
Pray and Obey Ministries
Flask marketing site + grant application intake.

All editable copy lives in this file as plain Python data structures.
Templates read from these, so content edits never require touching Jinja logic.
"""

import os
import time
import json
import logging
from datetime import datetime, timezone

import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "Pray and Obey <apply@prayandobey.org>")
MAIL_TO = os.environ.get("MAIL_TO", "info@prayandobey.org")

# Minimum seconds a human needs to fill the application form.
FORM_MIN_SECONDS = int(os.environ.get("FORM_MIN_SECONDS", "8"))

logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Site content
# ---------------------------------------------------------------------------

SITE = {
    "name": "Pray and Obey Ministries",
    "short_name": "Pray and Obey",
    "tagline": "Advancing hope for the vulnerable through compassionate giving.",
    "meta_description": (
        "Pray and Obey Ministries is a private fund providing grants to organizations "
        "committed to compassionate action for vulnerable individuals and communities."
    ),
    "domain": "https://prayandobey.org",
    "email": "info@prayandobey.org",
    "socials": [
        {"label": "Facebook", "handle": "prayandobeyministries", "url": "https://facebook.com/prayandobeyministries"},
        {"label": "Instagram", "handle": "prayandobeyministries", "url": "https://instagram.com/prayandobeyministries"},
        {"label": "YouTube", "handle": "prayandobeyministries", "url": "https://youtube.com/@prayandobeyministries"},
    ],
}

NAV = [
    {"label": "Mission", "href": "/#mission"},
    {"label": "What We Fund", "href": "/#what-we-fund"},
    {"label": "How It Works", "href": "/#how-it-works"},
    {"label": "FAQ", "href": "/#faq"},
]

HERO = {
    "headline_lead": "We support those who",
    "headline_accent": "serve the vulnerable.",
    "body": (
        "Pray and Obey Ministries provides grants to organizations committed to compassionate "
        "action for vulnerable individuals and communities. Together, we support the work that "
        "brings hope, dignity, and practical help to those who need it most."
    ),
    "primary_cta": {"label": "Apply for funding", "href": "/apply"},
    "secondary_cta": {"label": "See what we fund", "href": "/#what-we-fund"},
    "image": "img/hero.jpg",
    "image_alt": "A ministry team praying over a young girl",
    "float_card_top": {"label": "Funding type", "value": "Grants, not loans"},
    "float_card_bottom": {"label": "Where we give", "value": "U.S. and international"},
}

MISSION = {
    "eyebrow": "Our mission",
    "headline": "Glorify Jesus Christ by investing in the people who show up.",
    "body": (
        "Our mission is to glorify Jesus Christ by strategically investing in organizations that "
        "serve vulnerable individuals and communities. Through prayerful giving and grants, we "
        "support compassionate work that strengthens families, restores lives, and brings hope, "
        "dignity, and practical care to those in need."
    ),
    "image": "img/mission.jpg",
    "image_alt": "A group standing arm in arm in prayer",
    "badge_value": "Prayer first",
    "badge_label": "Every grant begins there",
    "pillars": [
        {
            "title": "How we give",
            "body": "Prayerfully, quietly, and directly to the organizations doing the work.",
        },
        {
            "title": "What we value",
            "body": "Compassion, faithfulness, sound stewardship, and lasting partnership.",
        },
    ],
    "cta": {"label": "Review our criteria", "href": "/#criteria"},
}

FOCUS = {
    "eyebrow": "What we fund",
    "headline": "Compassion guides every grant.",
    "intro": (
        "We seek to support organizations whose work reflects our commitment to serving vulnerable "
        "individuals and communities. We prioritize efforts that address physical, emotional, and "
        "spiritual needs while bringing hope, dignity, and practical support to those who need it most."
    ),
    "areas": [
        {
            "title": "Children and families",
            "body": "Programs that stabilize households, protect children, and strengthen family life.",
            "icon": "family",
        },
        {
            "title": "Those experiencing poverty",
            "body": "Relief and development work that meets immediate needs and builds a path forward.",
            "icon": "hands",
        },
        {
            "title": "The homeless and housing insecure",
            "body": "Shelter, transitional housing, and services that restore stability and dignity.",
            "icon": "home",
        },
        {
            "title": "Survivors of trafficking and exploitation",
            "body": "Rescue, aftercare, and long-term restoration for those coming out of exploitation.",
            "icon": "shield",
        },
        {
            "title": "The persecuted and vulnerable",
            "body": "Support for believers and communities under pressure, at home and abroad.",
            "icon": "cross",
        },
        {
            "title": "Whole-person care",
            "body": "Ministries treating physical, emotional, and spiritual need as one work.",
            "icon": "heart",
        },
        {
            "title": "Christian education",
            "body": "Schools and training that form character alongside knowledge.",
            "icon": "book",
        },
    ],
}

PROCESS = {
    "eyebrow": "How it works",
    "headline": "Four steps, start to finish.",
    "intro": "We keep the process simple. Here is exactly what happens after you apply.",
    "steps": [
        {
            "number": "01",
            "title": "Review the fit",
            "body": "Read through our focus areas and funding criteria to see whether your work aligns.",
        },
        {
            "number": "02",
            "title": "Submit your application",
            "body": "Complete the form. Most organizations finish it in about 15 to 20 minutes.",
        },
        {
            "number": "03",
            "title": "Quiet review",
            "body": "Our fund reviews every submission. We may follow up by email with a few clarifying questions.",
        },
        {
            "number": "04",
            "title": "Decision and partnership",
            "body": (
                "Organizations we are able to fund are contacted directly. Given volume, we cannot "
                "respond individually to every applicant."
            ),
        },
    ],
}

CRITERIA = {
    "eyebrow": "Criteria",
    "headline": "What we look for.",
    "intro": (
        "We are a small fund reviewing more requests than we can support. Clarity helps us both. "
        "Here is what moves an application forward."
    ),
    "looking_for": [
        "A clear, biblically grounded, Christ-centered mission",
        "Alignment with one or more of our focus areas",
        "An established track record and sound governance",
        "A specific, well-defined use for the funds requested",
    ],
    "good_to_know_title": "Good to know before applying",
    "good_to_know": [
        "Most partners are registered 501(c)(3) nonprofits, churches, or fiscally sponsored ministries",
        "We fund both one-time projects and ongoing operational needs",
        "We support work both in the U.S. and internationally",
        "We are a small, private fund and cannot support every request we receive",
    ],
}

FAQS = [
    {
        "q": "Do you fund internationally, or only in the U.S.?",
        "a": (
            "Both. Our compassion-focused giving supports work happening in local communities and "
            "around the world."
        ),
    },
    {
        "q": "Do we need to be a registered nonprofit to apply?",
        "a": (
            "Most of our partners are 501(c)(3) organizations, churches, or projects with a fiscal "
            "sponsor. If you are unsure whether your structure qualifies, apply and note your situation "
            "in the form. We will follow up if we need more information."
        ),
    },
    {
        "q": "Is this a grant, or a loan?",
        "a": "All funding is given as a grant. There is no repayment expected.",
    },
    {
        "q": "How long does the review process take?",
        "a": (
            "It varies with the volume of applications we receive, but most applicants hear back within "
            "several weeks. We are a small, private fund, so we appreciate your patience."
        ),
    },
    {
        "q": "Can we apply more than once?",
        "a": (
            "Yes. If your circumstances or programs change, you are welcome to submit a new application. "
            "We ask that you space repeat applications at least a year apart unless we have invited you "
            "to reapply sooner."
        ),
    },
    {
        "q": "Who is behind Pray and Obey Ministries?",
        "a": (
            "We are a private family fund. In keeping with our approach to giving, we do not publicize "
            "the individuals or family behind our support. Thank you for understanding if we keep those "
            "details private."
        ),
    },
]

CLOSING_CTA = {
    "eyebrow": "Take the next step",
    "headline": "Tell us about the work you are already doing.",
    "body": (
        "If your mission aligns with our focus areas, we would like to hear from you. The application "
        "takes most organizations about 15 to 20 minutes."
    ),
    "primary_cta": {"label": "Apply for funding", "href": "/apply"},
    "secondary_cta": {"label": "Read the FAQ", "href": "/#faq"},
}

FOOTER = {
    "explore": [
        {"label": "Mission", "href": "/#mission"},
        {"label": "What We Fund", "href": "/#what-we-fund"},
        {"label": "How It Works", "href": "/#how-it-works"},
    ],
    "apply": [
        {"label": "Funding Application", "href": "/apply"},
        {"label": "FAQ", "href": "/#faq"},
    ],
}

# ---------------------------------------------------------------------------
# Application form options
# ---------------------------------------------------------------------------

ORG_TYPES = [
    "501(c)(3) nonprofit",
    "Church",
    "Fiscally sponsored ministry",
    "International NGO",
    "Other",
]

FUNDING_TYPES = [
    "One-time project",
    "Ongoing operational support",
    "Both",
]

AMOUNT_RANGES = [
    "Under $5,000",
    "$5,000 to $15,000",
    "$15,000 to $50,000",
    "Over $50,000",
    "Not sure yet",
]

FOCUS_CHOICES = [a["title"] for a in FOCUS["areas"]]

REQUIRED_FIELDS = [
    ("org_name", "Organization name"),
    ("contact_name", "Contact name"),
    ("email", "Email address"),
    ("org_type", "Organization type"),
    ("mission", "Mission statement"),
    ("use_of_funds", "Use of funds"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def send_application_email(payload: dict) -> bool:
    """Send the application via the Resend HTTP API (port 443)."""
    if not RESEND_API_KEY:
        app.logger.warning("RESEND_API_KEY not set. Application logged only.")
        app.logger.info(json.dumps(payload, indent=2))
        return False

    rows = "".join(
        f"<tr>"
        f"<td style='padding:8px 14px;border-bottom:1px solid #e6e2d6;"
        f"font-family:Arial,sans-serif;font-size:13px;color:#0D2D5C;"
        f"font-weight:bold;vertical-align:top;white-space:nowrap;'>{k}</td>"
        f"<td style='padding:8px 14px;border-bottom:1px solid #e6e2d6;"
        f"font-family:Arial,sans-serif;font-size:13px;color:#222;'>{v or '-'}</td>"
        f"</tr>"
        for k, v in payload.items()
    )
    html = (
        f"<div style='background:#F7F2E6;padding:24px;'>"
        f"<h2 style='font-family:Arial,sans-serif;color:#0D2D5C;margin:0 0 16px;'>"
        f"New funding application</h2>"
        f"<table style='border-collapse:collapse;background:#fff;width:100%;max-width:640px;'>"
        f"{rows}</table></div>"
    )

    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": MAIL_FROM,
                "to": [MAIL_TO],
                "reply_to": payload.get("Email", MAIL_TO),
                "subject": f"Funding application: {payload.get('Organization', 'Unknown')}",
                "html": html,
            },
            timeout=15,
        )
        if r.status_code >= 400:
            app.logger.error("Resend error %s: %s", r.status_code, r.text)
            return False
        return True
    except requests.RequestException as exc:
        app.logger.error("Resend request failed: %s", exc)
        return False


def has_image(rel_path: str) -> bool:
    """True when a real photo has been dropped into static/.

    Photo slots render a branded navy panel until the client supplies imagery,
    so the site never shows a broken image on launch day.
    """
    if not rel_path:
        return False
    return os.path.isfile(os.path.join(app.static_folder, rel_path))


@app.context_processor
def inject_globals():
    return {
        "site": SITE,
        "nav": NAV,
        "footer": FOOTER,
        "current_year": datetime.now(timezone.utc).year,
        "has_image": has_image,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template(
        "index.html",
        hero=HERO,
        mission=MISSION,
        focus=FOCUS,
        process=PROCESS,
        criteria=CRITERIA,
        faqs=FAQS,
        closing=CLOSING_CTA,
    )


@app.route("/apply", methods=["GET", "POST"])
def apply_for_funding():
    form_data = {}

    if request.method == "POST":
        form_data = {k: (v or "").strip() for k, v in request.form.items()}

        # Honeypot: bots fill hidden fields.
        if form_data.get("website_url"):
            app.logger.info("Honeypot triggered on /apply")
            return redirect(url_for("thank_you"))

        # Timing check: submissions faster than a human are dropped.
        try:
            started = float(form_data.get("form_started", "0"))
        except ValueError:
            started = 0.0
        if started and (time.time() - started) < FORM_MIN_SECONDS:
            app.logger.info("Timing check triggered on /apply")
            return redirect(url_for("thank_you"))

        missing = [label for key, label in REQUIRED_FIELDS if not form_data.get(key)]
        if "@" not in form_data.get("email", ""):
            missing.append("A valid email address")

        if missing:
            flash("Please complete these fields: " + ", ".join(missing), "error")
        else:
            payload = {
                "Organization": form_data.get("org_name"),
                "Website": form_data.get("org_website"),
                "Organization type": form_data.get("org_type"),
                "EIN or tax ID": form_data.get("ein"),
                "Contact": form_data.get("contact_name"),
                "Role": form_data.get("contact_role"),
                "Email": form_data.get("email"),
                "Phone": form_data.get("phone"),
                "Location served": form_data.get("location"),
                "Focus areas": ", ".join(request.form.getlist("focus_areas")),
                "Funding type": form_data.get("funding_type"),
                "Amount requested": form_data.get("amount"),
                "Mission": form_data.get("mission"),
                "Use of funds": form_data.get("use_of_funds"),
                "Track record": form_data.get("track_record"),
                "How they heard": form_data.get("referral"),
                "Submitted": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            }
            send_application_email(payload)
            return redirect(url_for("thank_you"))

    return render_template(
        "apply.html",
        org_types=ORG_TYPES,
        funding_types=FUNDING_TYPES,
        amount_ranges=AMOUNT_RANGES,
        focus_choices=FOCUS_CHOICES,
        form_data=form_data,
        form_started=time.time(),
    )


@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
