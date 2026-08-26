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
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import (
    STATUSES,
    Application,
    User,
    database_uri,
    db,
    utcnow,
)

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") != "development"

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "portal_login"
login_manager.login_message = "Please sign in to view the portal."
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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
    # Not currently rendered. The footer Connect column was removed.
    # Re-adding the column in base.html will pick these up again.
    "socials": [
        {"label": "Facebook", "handle": "prayandobeyministries", "url": "https://facebook.com/prayandobeyministries"},
        {"label": "Instagram", "handle": "prayandobeyministries", "url": "https://instagram.com/prayandobeyministries"},
        {"label": "YouTube", "handle": "prayandobeyministries", "url": "https://youtube.com/@prayandobeyministries"},
    ],
}

NAV = [
    {"label": "About", "href": "/#about"},
    {"label": "Impact", "href": "/#impact"},
    {"label": "Mission", "href": "/#mission"},
    {"label": "What We Fund", "href": "/#what-we-fund"},
    {"label": "How It Works", "href": "/#how-it-works"},
    {"label": "FAQ", "href": "/#faq"},
]


HERO = {
    "eyebrow": "About",
    "headline_lead": "Faith that moves",
    "headline_accent": "us to give.",
    # Split into paragraphs so the hero reads as a story rather than one block.
    "body": [
        (
            "Pray and Obey Ministries is a Christian charitable fund conceived by a Christian "
            "family in Wilmington, North Carolina, with a desire to make a lasting Kingdom "
            "impact in their community and around the world."
        ),
        (
            "Guided by prayer, obedience to God's Word, and faithful stewardship, the ministry "
            "supports organizations and individuals who share the Gospel, serve those in need, "
            "strengthen communities, and advance Christ-centered work."
        ),
        (
            "Its mission is not only to make an impact today, but to establish a legacy of "
            "faith and generosity that will continue for generations to come."
        ),
    ],
    "primary_cta": {"label": "Apply for funding", "href": "/apply"},
    "secondary_cta": {"label": "What we fund", "href": "/#what-we-fund"},
    "tertiary_cta": {"label": "Our mission", "href": "/#mission"},
    "image": "img/hero.jpg",
    "image_alt": "A ministry team praying over a young girl",
}

IMPACT = {
    "eyebrow": "Our impact",
    "headline": "Key themes.",
    "areas": [
        {
            "number": "1",
            "title": "Proclaiming the Gospel of Jesus Christ",
            "body": (
                "Supporting ministries that clearly and faithfully share the message of Jesus, "
                "locally and globally, through evangelism, missions, Scripture distribution, and "
                "Christian media."
            ),
        },
        {
            "number": "2",
            "title": "Strengthening fathers, families, and biblical leadership",
            "body": (
                "Investing in organizations that model and encourage loving, Christ-centered "
                "fathers and strong families, recognizing their essential role in creating "
                "healthy communities."
            ),
        },
        {
            "number": "3",
            "title": "Compassion in action for the vulnerable",
            "body": (
                "Funding efforts that meet physical, emotional, and spiritual needs, including "
                "aid for the poor, persecuted Christians, victims of trafficking, the homeless, "
                "and children, demonstrating Christ's love through service."
            ),
        },
        {
            "number": "4",
            "title": "Light in darkness through media, education, and global reach",
            "body": (
                "Supporting Christian radio, television, education, and outreach tools that "
                "counter hatred and confusion with truth, unity, and hope rooted in Christ."
            ),
        },
    ],
    # Word cloud rendered as positioned text, not an image, so it stays sharp
    # at any density. "size" is in container-query width units and "top"/"left"
    # are percentages of the cloud box, which reproduces the client's scattered
    # arrangement while scaling with the container. Below 520px the words fall
    # back to a simple centered flow so nothing overlaps.
    "cloud": [
        {"word": "fathers",    "size": 3.7,  "top": 12, "left": 24, "tone": "muted"},
        {"word": "compassion", "size": 6.4,  "top": 22, "left": 5,  "tone": "muted"},
        {"word": "jesus",      "size": 10.4, "top": 33, "left": 10, "tone": "navy"},
        {"word": "service",    "size": 5.2,  "top": 60, "left": 17, "tone": "muted"},
        {"word": "love",       "size": 7.2,  "top": 49, "left": 45, "tone": "navy"},
        {"word": "faith",      "size": 9.8,  "top": 66, "left": 44, "tone": "navy"},
        {"word": "families",   "size": 4.4,  "top": 64, "left": 69, "tone": "muted"},
        {"word": "global",     "size": 3.3,  "top": 88, "left": 81, "tone": "muted"},
    ],
    "badge": "img/logo-badge.png",
    "badge_alt": "Pray and Obey Ministries seal",
    "statement_label": "Impact statement",
    "statement": (
        "Our mission is to glorify Jesus Christ by supporting ministries that bring His love and "
        "truth to the world, strengthening fathers and families, restoring lives through "
        "compassion and service, and boldly advancing the Gospel to replace hatred and discord "
        "with faith, hope, and reconciliation."
    ),
    # Client-supplied verse text. Because Scripture is quoted, Crossway's
    # attribution requirement applies. See SCRIPTURE_NOTICE below.
    "quote": (
        "He has told you, O man, what is good; and what does the Lord require of you but to do "
        "justice, and to love kindness, and to walk humbly with your God?"
    ),
    "quote_reference": "Micah 6:8",
    "quote_translation": "ESV",
    "guided_by": "Matthew 22:37-40 and Matthew 6:33, ESV.",
}

# Crossway requires this notice wherever ESV text is quoted. It renders directly
# beneath the quotation, since the site has no footer.
SCRIPTURE_NOTICE = (
    "Scripture quotation is from the ESV Bible (The Holy Bible, English Standard Version), "
    "copyright 2001 by Crossway, a publishing ministry of Good News Publishers. Used by "
    "permission. All rights reserved."
)


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

# ---------------------------------------------------------------------------
# Scripture references
# ---------------------------------------------------------------------------
#
# References only. No verse text is displayed, so no ESV license notice or
# attribution is required. Changing a reference here changes it on the page.

VERSES = {
    "mission": {"reference": "Matthew 22:37-40", "translation": "ESV"},
    "focus": {"reference": "Micah 6:8", "translation": "ESV"},
    "criteria": {"reference": "Matthew 6:33", "translation": "ESV"},
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
            "body": "Complete the form. Plan for about 30 minutes and have your project budget ready.",
        },
        {
            "number": "03",
            "title": "Review",
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
        "If your mission aligns with our focus areas, we would like to hear from you. Plan for about "
        "30 minutes and have your project budget and financial documents ready."
    ),
    "primary_cta": {"label": "Apply for funding", "href": "/apply"},
    "secondary_cta": {"label": "Read the FAQ", "href": "/#faq"},
}

# ---------------------------------------------------------------------------
# Application form options
# ---------------------------------------------------------------------------

ORG_TYPES = [
    "501(c)(3) public charity",
    "Church",
    "Fiscal sponsor",
    "International ministry",
    "Other",
]

PRIORITIES = [
    "Proclaiming the Gospel",
    "Strengthening fathers and families",
    "Serving vulnerable people",
    "Christian media or education",
    "Global outreach",
    "Bible / Scripture distribution",
]

BIBLE_WILLINGNESS = [
    "Yes, central activity",
    "Yes, supporting activity",
    "Willing with resources or training",
    "No",
]

ASSISTANCE_TYPES = [
    "Funding",
    "Bibles",
    "Translation support",
    "Training",
    "Distribution partner",
    "Other",
]

ATTACHMENTS = [
    "Tax-exempt or church documentation",
    "Most recent financial statement",
    "Current operating budget",
    "Project budget (if needed)",
    "Board member list",
    "Safeguarding policy (if applicable)",
]

BUDGET_ROWS = 5

CERTIFICATION_TEXT = (
    "I certify that this application and its attachments are accurate and complete; "
    "any grant funds will be used only for the approved charitable purpose; and material "
    "changes will be disclosed promptly. Submission does not guarantee funding."
)

# (field name, label shown in the validation message)
REQUIRED_FIELDS = [
    # Section 1: organization and request
    ("legal_name", "Legal organization name"),
    ("ein", "Federal EIN"),
    ("service_area", "Primary service area"),
    ("contact_name", "Primary contact and title"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("mailing_address", "Mailing address"),
    ("org_type", "Organization type"),
    ("mission_activities", "Ministry mission and principal activities"),
    ("gospel_sharing", "How your ministry shares the Gospel"),
    ("amount_requested", "Amount requested"),
    ("start_date", "Proposed start date"),
    ("end_date", "Proposed end date"),
    ("project_summary", "Summary of the project or request"),
    ("who_served", "Who will be served"),
    # Section 2: mission alignment and Bible distribution
    ("strongest_fit", "Strongest priority fit"),
    ("activities_timeline", "Main activities, timeline, and person responsible"),
    ("funds_use", "How the requested funds will be used"),
    ("bible_willingness", "Willingness to distribute Bibles or Scripture"),
    ("bible_description", "Proposed Bible or Scripture distribution"),
    ("scripture_engagement", "How recipients will engage with Scripture"),
    # Section 3: outcomes, finances, and certification
    ("expected_results", "Expected results and how you will measure them"),
    ("sustainability", "How the work continues after the grant ends"),
    ("authorized_rep", "Authorized representative"),
    ("rep_title", "Representative title"),
    ("signature", "Signature"),
    ("certify", "Certification agreement"),
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

    def row(k, v):
        if k.startswith("--"):
            label = k.strip("- ").title()
            return (
                f"<tr><td colspan='2' style='padding:18px 14px 8px;"
                f"font-family:Arial,sans-serif;font-size:11px;letter-spacing:1.4px;"
                f"text-transform:uppercase;color:#FFFFFF;background:#0D2D5C;"
                f"font-weight:bold;'>{label}</td></tr>"
            )
        return (
            f"<tr>"
            f"<td style='padding:8px 14px;border-bottom:1px solid #DCE3EE;"
            f"font-family:Arial,sans-serif;font-size:13px;color:#0D2D5C;"
            f"font-weight:bold;vertical-align:top;width:38%;'>{k}</td>"
            f"<td style='padding:8px 14px;border-bottom:1px solid #DCE3EE;"
            f"font-family:Arial,sans-serif;font-size:13px;color:#222;'>{v or '-'}</td>"
            f"</tr>"
        )

    rows = "".join(row(k, v) for k, v in payload.items())
    html = (
        f"<div style='background:#F2F5FA;padding:24px;'>"
        f"<h2 style='font-family:Arial,sans-serif;color:#0D2D5C;margin:0 0 16px;'>"
        f"New funding application</h2>"
        f"<table style='border-collapse:collapse;background:#fff;width:100%;max-width:720px;'>"
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
                "subject": f"Grant application: {payload.get('Legal organization name', 'Unknown')}",
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
        impact=IMPACT,
        scripture_notice=SCRIPTURE_NOTICE,
        mission=MISSION,
        focus=FOCUS,
        process=PROCESS,
        criteria=CRITERIA,
        verses=VERSES,
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
            budget_rows = []
            for i in range(BUDGET_ROWS):
                desc = form_data.get(f"budget_desc_{i}", "")
                total = form_data.get(f"budget_total_{i}", "")
                req = form_data.get(f"budget_request_{i}", "")
                if desc or total or req:
                    budget_rows.append(f"{desc} | total {total or '-'} | requested {req or '-'}")

            payload = {
                "-- 1. ORGANIZATION AND REQUEST --": "",
                "Legal organization name": form_data.get("legal_name"),
                "Doing-business-as name": form_data.get("dba_name"),
                "Federal EIN": form_data.get("ein"),
                "Year founded": form_data.get("year_founded"),
                "Website": form_data.get("org_website"),
                "Primary service area": form_data.get("service_area"),
                "Primary contact and title": form_data.get("contact_name"),
                "Email": form_data.get("email"),
                "Phone": form_data.get("phone"),
                "Mailing address": form_data.get("mailing_address"),
                "Organization type": form_data.get("org_type"),
                "Mission and principal activities": form_data.get("mission_activities"),
                "How the ministry shares the Gospel": form_data.get("gospel_sharing"),
                "Amount requested": form_data.get("amount_requested"),
                "Total project budget": form_data.get("total_project_budget"),
                "Proposed start date": form_data.get("start_date"),
                "Proposed end date": form_data.get("end_date"),
                "Project summary": form_data.get("project_summary"),
                "Who will be served": form_data.get("who_served"),

                "-- 2. MISSION ALIGNMENT AND BIBLE DISTRIBUTION --": "",
                "Priorities selected": ", ".join(request.form.getlist("priorities")),
                "Strongest fit": form_data.get("strongest_fit"),
                "Activities, timeline, responsible person": form_data.get("activities_timeline"),
                "Use of requested funds": form_data.get("funds_use"),
                "Willing to distribute Bibles": form_data.get("bible_willingness"),
                "Proposed distribution": form_data.get("bible_description"),
                "Scripture engagement and follow-up": form_data.get("scripture_engagement"),
                "Assistance requested": ", ".join(request.form.getlist("assistance")),

                "-- 3. OUTCOMES, FINANCES, AND CERTIFICATION --": "",
                "Expected results and measurement": form_data.get("expected_results"),
                "Sustainability after the grant": form_data.get("sustainability"),
                "Risks, safeguarding, legal, financial": form_data.get("risks"),
                "Budget lines": "<br>".join(budget_rows) if budget_rows else "-",
                "Budget total": form_data.get("budget_grand_total"),
                "Attachments confirmed ready": ", ".join(request.form.getlist("attachments")),
                "Authorized representative": form_data.get("authorized_rep"),
                "Title": form_data.get("rep_title"),
                "Signature (typed)": form_data.get("signature"),
                "Certified": "Yes" if form_data.get("certify") else "No",
                "Submitted": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            }
            record = Application(
                legal_name=form_data.get("legal_name"),
                dba_name=form_data.get("dba_name"),
                ein=form_data.get("ein"),
                year_founded=form_data.get("year_founded"),
                org_website=form_data.get("org_website"),
                service_area=form_data.get("service_area"),
                contact_name=form_data.get("contact_name"),
                email=form_data.get("email"),
                phone=form_data.get("phone"),
                mailing_address=form_data.get("mailing_address"),
                org_type=form_data.get("org_type"),
                mission_activities=form_data.get("mission_activities"),
                gospel_sharing=form_data.get("gospel_sharing"),
                amount_requested=form_data.get("amount_requested"),
                total_project_budget=form_data.get("total_project_budget"),
                start_date=form_data.get("start_date"),
                end_date=form_data.get("end_date"),
                project_summary=form_data.get("project_summary"),
                who_served=form_data.get("who_served"),
                priorities=", ".join(request.form.getlist("priorities")),
                strongest_fit=form_data.get("strongest_fit"),
                activities_timeline=form_data.get("activities_timeline"),
                funds_use=form_data.get("funds_use"),
                bible_willingness=form_data.get("bible_willingness"),
                bible_description=form_data.get("bible_description"),
                scripture_engagement=form_data.get("scripture_engagement"),
                assistance=", ".join(request.form.getlist("assistance")),
                expected_results=form_data.get("expected_results"),
                sustainability=form_data.get("sustainability"),
                risks=form_data.get("risks"),
                budget_lines="\n".join(budget_rows),
                budget_grand_total=form_data.get("budget_grand_total"),
                attachments=", ".join(request.form.getlist("attachments")),
                authorized_rep=form_data.get("authorized_rep"),
                rep_title=form_data.get("rep_title"),
                signature=form_data.get("signature"),
                certified=bool(form_data.get("certify")),
            )
            try:
                db.session.add(record)
                db.session.commit()
            except Exception as exc:  # noqa: BLE001
                db.session.rollback()
                app.logger.error("Could not save application: %s", exc)

            # Email remains the backup path. A database write failure must not
            # cost the applicant their submission.
            send_application_email(payload)
            return redirect(url_for("thank_you"))

    return render_template(
        "apply.html",
        org_types=ORG_TYPES,
        priorities=PRIORITIES,
        bible_willingness=BIBLE_WILLINGNESS,
        assistance_types=ASSISTANCE_TYPES,
        attachments=ATTACHMENTS,
        budget_rows=range(BUDGET_ROWS),
        certification_text=CERTIFICATION_TEXT,
        form_data=form_data,
        form_started=time.time(),
    )


@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")


# ---------------------------------------------------------------------------
# Portal
# ---------------------------------------------------------------------------


@app.route("/portal/login", methods=["GET", "POST"])
def portal_login():
    if current_user.is_authenticated:
        return redirect(url_for("portal"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = db.session.query(User).filter(User.email == email).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=False)
            user.last_login_at = utcnow()
            db.session.commit()
            nxt = request.args.get("next")
            # Only allow relative redirects, never an external host.
            if nxt and nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect(url_for("portal"))

        # Same message either way, so the form cannot be used to discover
        # which email addresses have accounts.
        flash("That email and password combination was not recognized.", "error")

    return render_template("portal_login.html")


@app.route("/portal/logout")
@login_required
def portal_logout():
    logout_user()
    return redirect(url_for("portal_login"))


@app.route("/portal")
@login_required
def portal():
    status_filter = request.args.get("status", "All")
    query = db.session.query(Application)
    if status_filter in STATUSES:
        query = query.filter(Application.status == status_filter)

    applications = query.order_by(Application.submitted_at.desc()).all()

    counts = {"All": db.session.query(Application).count()}
    for st in STATUSES:
        counts[st] = db.session.query(Application).filter(Application.status == st).count()

    return render_template(
        "portal_list.html",
        applications=applications,
        statuses=STATUSES,
        counts=counts,
        status_filter=status_filter,
    )


@app.route("/portal/application/<int:app_id>")
@login_required
def portal_application(app_id):
    record = db.session.get(Application, app_id)
    if record is None:
        abort(404)
    return render_template(
        "portal_detail.html",
        a=record,
        statuses=STATUSES,
    )


@app.route("/portal/application/<int:app_id>/status", methods=["POST"])
@login_required
def portal_update_status(app_id):
    record = db.session.get(Application, app_id)
    if record is None:
        abort(404)

    new_status = request.form.get("status")
    notes = (request.form.get("reviewer_notes") or "").strip()

    if new_status in STATUSES and new_status != record.status:
        record.status = new_status
        record.status_changed_at = utcnow()
        record.status_changed_by = current_user.name
        flash(f"Status set to {new_status}.", "success")
    elif new_status not in STATUSES:
        flash("That status is not recognized.", "error")

    if notes != (record.reviewer_notes or ""):
        record.reviewer_notes = notes
        flash("Notes saved.", "success")

    db.session.commit()
    return redirect(url_for("portal_application", app_id=app_id))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@app.cli.command("init-db")
def init_db():
    """Create database tables. Safe to run more than once."""
    db.create_all()
    print("Tables created.")


@app.cli.command("create-user")
def create_user():
    """Create a portal user. Prompts for name, email, and password."""
    import getpass

    name = input("Name: ").strip()
    email = input("Email: ").strip().lower()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        return
    if len(password) < 12:
        print("Use at least 12 characters.")
        return
    if db.session.query(User).filter(User.email == email).first():
        print("A user with that email already exists.")
        return

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Created portal user {email}.")


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
