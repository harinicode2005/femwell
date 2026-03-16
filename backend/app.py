import os
import random
import smtplib
from io import BytesIO
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import mysql.connector
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PROJECT_DIR = BASE_DIR.parent

app = FastAPI(title="FemWell")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "my_super_secure_femwell_key_123"),
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


OTP_STORAGE: dict[str, str] = {}
PASSWORD_RESET_OTP_STORAGE: dict[str, tuple[str, datetime]] = {}
WELLNESS_TIPS = [
    "Drink warm water to support digestion.",
    "Sleep at least 7-8 hours for hormone balance.",
    "Avoid excess sugar today.",
    "Do 10 minutes of breathing exercises.",
    "Stay hydrated throughout the day.",
]
DIET_PLANS = {
    "days-1-14": {
        "label": "Days 1 - 14",
        "title": "Follicular Phase Diet Plan",
        "description": "A lighter first-phase plan with iron, fiber, and steady protein.",
        "pdf_filename": "Day1-To-Day14-Healthy-Plan.pdf",
        "items": [
            {"name": "Spinach Bowl", "desc": "Iron-rich greens with lentils and lemon."},
            {"name": "Oats and Seeds", "desc": "Slow carbs with flax and pumpkin seeds."},
            {"name": "Greek Yogurt", "desc": "Protein support with berries for digestion."},
            {"name": "Boiled Eggs", "desc": "Simple protein to keep energy stable."},
        ],
    },
    "30-days": {
        "label": "30 Days",
        "title": "30-Day Hormone Balance Plan",
        "description": "A balanced month-long routine built around low GI carbs and anti-inflammatory meals.",
        "pdf_filename": "30-Day-Healthy-Diet-Journey.pdf",
        "items": [
            {"name": "Brown Rice Plate", "desc": "Low GI grains with vegetables and tofu."},
            {"name": "Curd and Cucumber", "desc": "Gut-friendly cooling side dish."},
            {"name": "Mixed Nuts", "desc": "Healthy fats for hormone balance."},
            {"name": "Vegetable Soup", "desc": "Light dinner option with minerals and fiber."},
        ],
    },
    "45-days": {
        "label": "45 Days",
        "title": "45-Day PCOD Care Plan",
        "description": "A more structured plan for longer cycle support with simple repeatable meals.",
        "pdf_filename": "Day1-To-Day45-Healthy-Plan.pdf",
        "items": [
            {"name": "Millet Breakfast", "desc": "High-fiber breakfast to support insulin control."},
            {"name": "Paneer Salad", "desc": "Protein-rich lunch with fresh vegetables."},
            {"name": "Herbal Tea", "desc": "Spearmint or cinnamon tea between meals."},
            {"name": "Light Dinner", "desc": "Khichdi or soup-based meal to reduce inflammation."},
        ],
    },
}


@app.on_event("startup")
async def startup_event() -> None:
    ensure_user_details_schema()


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "NewStrongPassword123!"),
        database=os.getenv("DB_NAME", "femwell"),
    )


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()


def execute_query(query: str, params: tuple[Any, ...] = ()) -> None:
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        db.commit()
    finally:
        cursor.close()
        db.close()


def parse_int_field(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return int(cleaned)


def parse_float_field(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return float(cleaned)


def ensure_user_details_schema() -> None:
    database_name = os.getenv("DB_NAME", "femwell")
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_details (
                user_id INT NOT NULL PRIMARY KEY,
                age INT NULL,
                height_cm DECIMAL(5,2) NULL,
                weight_kg DECIMAL(5,2) NULL,
                last_period_date DATE NULL,
                target_plan_key VARCHAR(40) NULL,
                target_duration_days INT NULL,
                target_start_date DATE NULL,
                cycle_length_days INT NULL,
                period_duration_days INT NULL,
                health_issues TEXT NULL,
                common_symptoms TEXT NULL,
                diagnosis_status VARCHAR(120) NULL,
                medications TEXT NULL,
                activity_level VARCHAR(50) NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )

        required_columns = {
            "age": "ALTER TABLE user_details ADD COLUMN age INT NULL",
            "height_cm": "ALTER TABLE user_details ADD COLUMN height_cm DECIMAL(5,2) NULL",
            "weight_kg": "ALTER TABLE user_details ADD COLUMN weight_kg DECIMAL(5,2) NULL",
            "last_period_date": "ALTER TABLE user_details ADD COLUMN last_period_date DATE NULL",
            "target_plan_key": "ALTER TABLE user_details ADD COLUMN target_plan_key VARCHAR(40) NULL",
            "target_duration_days": "ALTER TABLE user_details ADD COLUMN target_duration_days INT NULL",
            "target_start_date": "ALTER TABLE user_details ADD COLUMN target_start_date DATE NULL",
            "cycle_length_days": "ALTER TABLE user_details ADD COLUMN cycle_length_days INT NULL",
            "period_duration_days": "ALTER TABLE user_details ADD COLUMN period_duration_days INT NULL",
            "health_issues": "ALTER TABLE user_details ADD COLUMN health_issues TEXT NULL",
            "common_symptoms": "ALTER TABLE user_details ADD COLUMN common_symptoms TEXT NULL",
            "diagnosis_status": "ALTER TABLE user_details ADD COLUMN diagnosis_status VARCHAR(120) NULL",
            "medications": "ALTER TABLE user_details ADD COLUMN medications TEXT NULL",
            "activity_level": "ALTER TABLE user_details ADD COLUMN activity_level VARCHAR(50) NULL",
            "created_at": "ALTER TABLE user_details ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "ALTER TABLE user_details ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        }

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema=%s AND table_name='user_details'
            """,
            (database_name,),
        )
        existing_columns = {row[0] for row in cursor.fetchall()}

        for column_name, ddl in required_columns.items():
            if column_name not in existing_columns:
                cursor.execute(ddl)

        db.commit()
    finally:
        cursor.close()
        db.close()


def render(request: Request, template_name: str, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=303)


def send_welcome_email(user_email: str, user_name: str) -> None:
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        return

    body = f"""
Hi {user_name},

Welcome to FemWell.

Your wellness journey starts here.

FemWell helps women manage PCOD/PCOS through:
- Cycle tracking
- Diet plans
- Exercise guidance
- Emotional wellness support

Stay healthy and take care.

Team FemWell
""".strip()

    msg = MIMEText(body)
    msg["Subject"] = "Welcome to FemWell"
    msg["From"] = sender_email
    msg["To"] = user_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
    except Exception:
        pass


def send_contact_email(sender_name: str, sender_email: str, message: str) -> tuple[bool, str | None]:
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    support_email = os.getenv("SUPPORT_EMAIL", "supportfemwell@gmail.com")

    if not smtp_email or not smtp_password:
        return False, "Email sending is not configured yet. Please add SMTP credentials."

    body = f"""
New contact message from FemWell.

Name: {sender_name}
Email: {sender_email}

Message:
{message}
""".strip()

    msg = MIMEText(body)
    msg["Subject"] = f"FemWell Contact Form: {sender_name}"
    msg["From"] = smtp_email
    msg["To"] = support_email
    msg["Reply-To"] = sender_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, support_email, msg.as_string())
        server.quit()
        return True, None
    except Exception as exc:
        print(f"Contact email send failed: {exc}")
        return False, "Unable to send your message right now. Please try again later."


def send_password_reset_email(user_email: str, otp: str) -> tuple[bool, str | None]:
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        return False, "Email sending is not configured yet. Please add SMTP credentials."

    body = f"""
Hi,

Your FemWell password reset OTP is: {otp}

This OTP is valid for 10 minutes.
If you did not request a password reset, you can ignore this email.

Team FemWell
""".strip()

    msg = MIMEText(body)
    msg["Subject"] = "FemWell Password Reset OTP"
    msg["From"] = sender_email
    msg["To"] = user_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        return True, None
    except Exception as exc:
        print(f"Password reset email send failed: {exc}")
        return False, "Unable to send OTP right now. Please try again later."


def get_current_user(request: Request) -> dict[str, Any] | None:
    user_identifier = request.session.get("user")
    if not user_identifier:
        return None

    return fetch_one(
        "SELECT * FROM users WHERE email=%s OR mobile=%s",
        (user_identifier, user_identifier),
    )


def calculate_cycle_day(last_period_date: date | None) -> int | None:
    if last_period_date is None:
        return None
    return max((date.today() - last_period_date).days, 0)


def get_plan_duration(plan_key: str) -> int:
    if plan_key in DIET_PLANS:
        key_numbers = "".join(ch if ch.isdigit() else " " for ch in plan_key).split()
        if key_numbers:
            return max(int(value) for value in key_numbers)

        label = str(DIET_PLANS[plan_key].get("label", ""))
        label_numbers = "".join(ch if ch.isdigit() else " " for ch in label).split()
        if label_numbers:
            return max(int(value) for value in label_numbers)

    return 45


def build_wellness_pdf(user_name: str, cycle_day: int | None, tip: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="FemWell Guide")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FemWellTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#ff6f91"),
        spaceAfter=18,
    )
    body_style = ParagraphStyle(
        "FemWellBody",
        parent=styles["BodyText"],
        fontSize=12,
        leading=18,
        spaceAfter=12,
    )

    cycle_text = f"Day {cycle_day} / 45" if cycle_day is not None else "Not recorded yet"
    story = [
        Paragraph("<b>FemWell Wellness Summary</b>", title_style),
        Paragraph(
            f"<b>User:</b> {user_name}<br/><b>Current cycle:</b> {cycle_text}",
            body_style,
        ),
        Paragraph("<u><b>Food Guidance</b></u>", body_style),
        Paragraph(
            "Choose <b>fiber-rich foods</b>, balanced protein, and steady hydration to support hormones.",
            body_style,
        ),
        Paragraph("<u><b>Exercise and Yoga</b></u>", body_style),
        Paragraph(
            "Use <i>gentle movement</i> such as walking, stretching, and beginner yoga on most days.",
            body_style,
        ),
        Paragraph("<u><b>Today's Wellness Tip</b></u>", body_style),
        Paragraph(f"<i>{tip}</i>", body_style),
        Spacer(1, 12),
        Paragraph(
            "<b>Note:</b> If your cycle extends beyond 45 days, consult a doctor for proper medical advice.",
            body_style,
        ),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer


def build_diet_pdf(plan_key: str) -> BytesIO:
    plan = DIET_PLANS[plan_key]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=plan["title"])
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DietTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#6B4EFF"),
        spaceAfter=18,
    )
    body_style = ParagraphStyle(
        "DietBody",
        parent=styles["BodyText"],
        fontSize=12,
        leading=18,
        spaceAfter=10,
    )

    story = [
        Paragraph(f"<b>{plan['title']}</b>", title_style),
        Paragraph(f"<i>{plan['description']}</i>", body_style),
        Paragraph("<u><b>Diet Plan Summary</b></u>", body_style),
    ]

    for item in plan["items"]:
        story.append(Paragraph(f"<b>{item['name']}</b>: {item['desc']}", body_style))

    story.append(
        Paragraph(
            "<u><b>Guidance</b></u><br/>Drink water regularly, avoid excess sugar, and stay consistent with meals.",
            body_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return render(request, "index.html")


@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request) -> HTMLResponse:
    return render(request, "signin.html", error=None, message=None)


@app.post("/signin", response_class=HTMLResponse)
async def signin(
    request: Request,
    login_id: str = Form(...),
    password: str = Form(""),
) -> Response:
    user = fetch_one("SELECT * FROM users WHERE email=%s", (login_id,))
    if user and user.get("password"):
        if not password or not check_password_hash(user["password"], password):
            return render(
                request,
                "signin.html",
                error="Incorrect password. Please try again.",
                message=None,
            )

    if not user:
        user = fetch_one("SELECT * FROM users WHERE mobile=%s", (login_id,))

    if not user:
        return render(
            request,
            "signin.html",
            error="User not found. Please create an account.",
            message=None,
        )

    request.session["user"] = user.get("email") or user.get("mobile")
    return redirect("/dashboard")


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request) -> HTMLResponse:
    return render(request, "signup.html", error=None)


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request) -> HTMLResponse:
    return render(request, "forgot_password.html", error=None, success=None, email="")


@app.post("/forgot-password/send-otp", response_class=HTMLResponse)
async def forgot_password_send_otp(request: Request, email: str = Form(...)) -> HTMLResponse:
    normalized_email = email.strip().lower()
    if not normalized_email:
        return render(
            request,
            "forgot_password.html",
            error="Please enter your email.",
            success=None,
            email="",
        )

    user = fetch_one("SELECT id, password FROM users WHERE email=%s", (normalized_email,))
    if not user or not user.get("password"):
        return render(
            request,
            "forgot_password.html",
            error="No password-based account found for this email.",
            success=None,
            email=normalized_email,
        )

    otp = str(random.randint(100000, 999999))
    PASSWORD_RESET_OTP_STORAGE[normalized_email] = (otp, datetime.utcnow() + timedelta(minutes=10))
    sent, error_message = send_password_reset_email(normalized_email, otp)
    if not sent:
        return render(
            request,
            "forgot_password.html",
            error=error_message,
            success=None,
            email=normalized_email,
        )

    return render(
        request,
        "forgot_password.html",
        error=None,
        success="OTP sent to your email. It is valid for 10 minutes.",
        email=normalized_email,
    )


@app.post("/forgot-password/reset", response_class=HTMLResponse)
async def forgot_password_reset(
    request: Request,
    email: str = Form(...),
    otp: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
) -> HTMLResponse:
    normalized_email = email.strip().lower()
    stored = PASSWORD_RESET_OTP_STORAGE.get(normalized_email)
    if not stored:
        return render(
            request,
            "forgot_password.html",
            error="OTP not found or expired. Please request a new OTP.",
            success=None,
            email=normalized_email,
        )

    stored_otp, expires_at = stored
    if datetime.utcnow() > expires_at:
        PASSWORD_RESET_OTP_STORAGE.pop(normalized_email, None)
        return render(
            request,
            "forgot_password.html",
            error="OTP expired. Please request a new OTP.",
            success=None,
            email=normalized_email,
        )

    if otp.strip() != stored_otp:
        return render(
            request,
            "forgot_password.html",
            error="Invalid OTP.",
            success=None,
            email=normalized_email,
        )

    if new_password != confirm_password:
        return render(
            request,
            "forgot_password.html",
            error="Password and confirm password must match.",
            success=None,
            email=normalized_email,
        )

    if len(new_password.strip()) < 6:
        return render(
            request,
            "forgot_password.html",
            error="Password must be at least 6 characters.",
            success=None,
            email=normalized_email,
        )

    user = fetch_one("SELECT id FROM users WHERE email=%s", (normalized_email,))
    if not user:
        return render(
            request,
            "forgot_password.html",
            error="User not found for this email.",
            success=None,
            email=normalized_email,
        )

    execute_query(
        "UPDATE users SET password=%s WHERE email=%s",
        (generate_password_hash(new_password), normalized_email),
    )
    PASSWORD_RESET_OTP_STORAGE.pop(normalized_email, None)
    return render(
        request,
        "signin.html",
        error=None,
        message="Password reset successful. Please sign in.",
    )


@app.post("/send_otp", response_class=PlainTextResponse)
async def send_otp(mobile: str = Form(...)) -> PlainTextResponse:
    otp = str(random.randint(1000, 9999))
    OTP_STORAGE[mobile] = otp
    return PlainTextResponse(f"OTP sent successfully. Your OTP is {otp}")


@app.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    name: str = Form(...),
    method: str = Form(...),
    email: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form(""),
    mobile: str = Form(""),
    otp: str = Form(""),
) -> Response:
    if method == "email":
        if not email or not password or not confirm_password:
            return render(
                request,
                "signup.html",
                error="Email, password, and confirm password are required.",
            )

        if password != confirm_password:
            return render(
                request,
                "signup.html",
                error="Password and confirm password must match.",
            )

        existing_user = fetch_one("SELECT id FROM users WHERE email=%s", (email,))
        if existing_user:
            return render(
                request,
                "signin.html",
                error="Email already registered. Please sign in.",
            )

        execute_query(
            "INSERT INTO users(name, email, password) VALUES(%s, %s, %s)",
            (name, email, generate_password_hash(password)),
        )
        request.session["user"] = email
        request.session["show_tracker_popup"] = True
        send_welcome_email(email, name)
        return redirect("/dashboard")

    if method == "mobile":
        if not mobile or not otp:
            return render(
                request,
                "signup.html",
                error="Mobile number and OTP are required.",
            )

        existing_user = fetch_one("SELECT id FROM users WHERE mobile=%s", (mobile,))
        if existing_user:
            return render(
                request,
                "signin.html",
                error="Mobile number already registered. Please sign in.",
            )

        if OTP_STORAGE.get(mobile) != otp:
            return render(request, "signup.html", error="Invalid OTP.")

        execute_query(
            "INSERT INTO users(name, mobile) VALUES(%s, %s)",
            (name, mobile),
        )
        OTP_STORAGE.pop(mobile, None)
        request.session["user"] = mobile
        request.session["show_tracker_popup"] = True
        return redirect("/dashboard")

    return render(request, "signup.html", error="Please choose a valid signup method.")


@app.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return redirect("/")


@app.get("/details", response_class=HTMLResponse)
async def details_page(request: Request) -> Response:
    if not get_current_user(request):
        return redirect("/signin")
    return redirect("/dashboard")


@app.post("/details", response_class=HTMLResponse)
async def details(
    request: Request,
    age: str = Form(""),
    height_cm: str = Form(""),
    weight_kg: str = Form(""),
    last_period_date: str = Form(""),
    cycle_length_days: str = Form(""),
    period_duration_days: str = Form(""),
    health_issues: str = Form(""),
    common_symptoms: str = Form(""),
    diagnosis_status: str = Form(""),
    medications: str = Form(""),
    activity_level: str = Form(""),
    selected_plan: str = Form(""),
) -> Response:
    user = get_current_user(request)
    if not user:
        return redirect("/signin")

    parsed_date = None
    if last_period_date.strip():
        try:
            parsed_date = datetime.strptime(last_period_date, "%Y-%m-%d").date()
        except ValueError:
            return redirect("/dashboard")

    target_plan_key: str | None = None
    target_duration_days: int | None = None
    target_start_date: date | None = None
    if selected_plan in DIET_PLANS and parsed_date is not None:
        target_plan_key = selected_plan
        target_duration_days = get_plan_duration(selected_plan)

    existing_details = fetch_one(
        "SELECT * FROM user_details WHERE user_id=%s",
        (user["id"],),
    )
    if target_plan_key:
        previous_plan_key = existing_details["target_plan_key"] if existing_details else None
        previous_start_date = existing_details["target_start_date"] if existing_details else None
        if previous_plan_key == target_plan_key and previous_start_date and parsed_date >= previous_start_date:
            target_start_date = previous_start_date
        else:
            target_start_date = parsed_date

    try:
        payload: dict[str, Any] = {
            "age": parse_int_field(age),
            "height_cm": parse_float_field(height_cm),
            "weight_kg": parse_float_field(weight_kg),
            "last_period_date": parsed_date,
            "target_plan_key": target_plan_key,
            "target_duration_days": target_duration_days,
            "target_start_date": target_start_date,
            "cycle_length_days": parse_int_field(cycle_length_days),
            "period_duration_days": parse_int_field(period_duration_days),
            "health_issues": health_issues.strip() or None,
            "common_symptoms": common_symptoms.strip() or None,
            "diagnosis_status": diagnosis_status.strip() or None,
            "medications": medications.strip() or None,
            "activity_level": activity_level.strip() or None,
        }
    except ValueError:
        return redirect("/dashboard")

    if existing_details:
        assignments = []
        values: list[Any] = []
        for key, value in payload.items():
            if value is not None:
                assignments.append(f"{key}=%s")
                values.append(value)

        if assignments:
            values.append(user["id"])
            execute_query(
                f"UPDATE user_details SET {', '.join(assignments)} WHERE user_id=%s",
                tuple(values),
            )
    else:
        execute_query(
            """
            INSERT INTO user_details (
                user_id,
                age,
                height_cm,
                weight_kg,
                last_period_date,
                target_plan_key,
                target_duration_days,
                target_start_date,
                cycle_length_days,
                period_duration_days,
                health_issues,
                common_symptoms,
                diagnosis_status,
                medications,
                activity_level
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user["id"],
                payload["age"],
                payload["height_cm"],
                payload["weight_kg"],
                payload["last_period_date"],
                payload["target_plan_key"],
                payload["target_duration_days"],
                payload["target_start_date"],
                payload["cycle_length_days"],
                payload["period_duration_days"],
                payload["health_issues"],
                payload["common_symptoms"],
                payload["diagnosis_status"],
                payload["medications"],
                payload["activity_level"],
            ),
        )
    request.session["show_tracker_popup"] = False
    return redirect("/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    user = get_current_user(request)
    if not user:
        return redirect("/signin")

    user_details = fetch_one(
        "SELECT * FROM user_details WHERE user_id=%s",
        (user["id"],),
    )
    last_period_date = user_details["last_period_date"] if user_details else None
    target_start_date = user_details["target_start_date"] if user_details else None
    target_duration_days = user_details["target_duration_days"] if user_details else None
    target_plan_key = user_details["target_plan_key"] if user_details else None

    cycle_day = calculate_cycle_day(last_period_date)
    if last_period_date and target_start_date and target_duration_days:
        tracked_day = (last_period_date - target_start_date).days + 1
        cycle_day = min(max(tracked_day, 1), int(target_duration_days))

    selected_default_plan = target_plan_key if target_plan_key in DIET_PLANS else "days-1-14"
    show_tracker_popup = bool(request.session.pop("show_tracker_popup", False))

    return render(
        request,
        "dashboard.html",
        name=user.get("name", "User"),
        cycle_day=cycle_day,
        tip=random.choice(WELLNESS_TIPS),
        diet_plans=DIET_PLANS,
        default_plan=selected_default_plan,
        tracker_details=user_details,
        show_tracker_popup=show_tracker_popup,
    )


@app.get("/download-pdf")
async def download_pdf(request: Request) -> Response:
    user = get_current_user(request)
    if not user:
        return redirect("/signin")

    user_details = fetch_one(
        "SELECT last_period_date FROM user_details WHERE user_id=%s",
        (user["id"],),
    )
    last_period_date = user_details["last_period_date"] if user_details else None
    cycle_day = calculate_cycle_day(last_period_date)
    tip = random.choice(WELLNESS_TIPS)
    pdf_buffer = build_wellness_pdf(user.get("name", "User"), cycle_day, tip)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="femwell-guide.pdf"'},
    )


@app.get("/food", response_class=HTMLResponse)
async def food_page(request: Request) -> HTMLResponse:
    selected_plan = request.query_params.get("plan", "days-1-14")
    if selected_plan not in DIET_PLANS:
        selected_plan = "days-1-14"
    return render(
        request,
        "food.html",
        diet_plans=DIET_PLANS,
        default_plan=selected_plan,
    )


@app.get("/download-diet-pdf/{plan_key}")
async def download_diet_pdf(plan_key: str) -> Response:
    if plan_key not in DIET_PLANS:
        return PlainTextResponse("Diet plan not found.", status_code=404)

    pdf_path = PROJECT_DIR / DIET_PLANS[plan_key]["pdf_filename"]
    if pdf_path.exists():
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=pdf_path.name,
        )

    pdf_buffer = build_diet_pdf(plan_key)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{plan_key}-diet-plan.pdf"'},
    )


@app.get("/seedcycling", response_class=HTMLResponse)
async def seedcycling_page(request: Request) -> HTMLResponse:
    return render(request, "seedcycling.html")


@app.get("/excercise", response_class=HTMLResponse)
async def exercise_page(request: Request) -> HTMLResponse:
    return render(request, "excercise.html")


@app.get("/wellness", response_class=HTMLResponse)
async def wellness_page(request: Request) -> HTMLResponse:
    return render(request, "wellness.html")


@app.get("/contect", response_class=HTMLResponse)
async def contact_page(request: Request) -> HTMLResponse:
    return render(
        request,
        "contect.html",
        success=None,
        error=None,
        form_data={"name": "", "email": "", "message": ""},
    )


@app.post("/contect", response_class=HTMLResponse)
async def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
) -> HTMLResponse:
    form_data = {
        "name": name.strip(),
        "email": email.strip(),
        "message": message.strip(),
    }

    if not all(form_data.values()):
        return render(
            request,
            "contect.html",
            success=None,
            error="Please fill in all fields before sending your message.",
            form_data=form_data,
        )

    sent, error_message = send_contact_email(
        sender_name=form_data["name"],
        sender_email=form_data["email"],
        message=form_data["message"],
    )

    if not sent:
        return render(
            request,
            "contect.html",
            success=None,
            error=error_message,
            form_data=form_data,
        )

    return render(
        request,
        "contect.html",
        success="Your message was sent successfully. We'll get back to you soon.",
        error=None,
        form_data={"name": "", "email": "", "message": ""},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
