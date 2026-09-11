import os
import uuid
import random
import secrets
import re
import csv
import io
import html
import time
import base64
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error as MySQLError
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
load_dotenv()
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "HND26"),
    "port": int(os.environ.get("DB_PORT", "3306")),
}

# Cameroon MTN prefixes (9-digit local numbers)
MTN_CAMEROON_PREFIXES = {
    "650", "651", "652", "653", "654",
    "670", "671", "672", "673", "674",
    "675", "676", "677", "678", "679",
    "680",
}

# Cameroon Orange prefixes (9-digit local numbers)
ORANGE_CAMEROON_PREFIXES = {
    "689", "690", "691", "692", "694",
    "695", "696", "697", "698", "699",
}

APP_SECRET = os.environ.get("APP_SECRET", "dev-secret-change")
APP_SCHOOL_NAME = os.environ.get("APP_SCHOOL_NAME", "IUGET")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")
SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587") or 587)
SMTP_USER = os.environ.get("SMTP_USER", "").strip()
SMTP_PASS = os.environ.get("SMTP_PASS", "").strip()
SMTP_SENDER = os.environ.get("SMTP_SENDER", "").strip() or SMTP_USER
PAYMENT_SIM_PIN = "12345"
MIN_PAYMENT_XAF = 50.0
CONTACT_RATE_WINDOW_MINUTES = 15
CONTACT_RATE_MAX_MESSAGES = 3
SUPPORTED_LANGS = {"en", "fr"}
COURSE_OPTIONS = sorted(
    [
        "Accounting",
        "Banking and Finance",
        "Business Management",
        "Civil Engineering",
        "Computer Engineering",
        "Computer Science",
        "Electrical Engineering",
        "Human Resource Management",
        "Information Technology",
        "Logistics and Transport",
        "Marketing",
        "Mechanical Engineering",
        "Network and Security",
        "Project Management",
        "Software Engineering",
        "Other",
    ],
    key=str.lower,
)
DEFAULT_YEARLY_FEE_XAF = 450000
DEFAULT_INSTALLMENT_SPLIT = (0.4, 0.35, 0.25)
DEFAULT_DEPARTMENTS: list[str] = []
TRANSLATIONS = {
    "en": {
        "brand": "IUGET Fee Portal",
        "home": "Home",
        "student_portal": "Student Portal",
        "make_payment": "Make Payment",
        "admin_portal": "Admin Portal",
        "payments": "Payments",
        "students": "Students",
        "logout": "Logout",
        "login": "Login",
        "register": "Register",
        "welcome_back": "Welcome Back",
        "login_in_subtitle": "login in to your school fee payment account.",
        "email_or_matricule": "Email or Matricule",
        "password": "Password",
        "login_in": "Log In",
        "create_account": "Create Student Account",
        "register_subtitle": "Fill in your details to start paying school fees online.",
        "full_name": "Full Name",
        "date_of_birth": "Date of Birth",
        "specialty": "Specialty / Department",
        "level_or_program": "Level or Program",
        "phone_mtn": "Phone Number (MTN)",
        "phone_number": "Phone Number",
        "school_name": "School Name",
        "matricule": "Matricule",
        "email": "Email",
        "create_account_btn": "Create Account",
        "pay_confidence": "Pay Your School Fees With Confidence",
        "lead_text": "A professional payment portal for students to complete school fee payments with MTN MoMo or Orange Money and receive instant receipts.",
        "create_student_account": "Create Student Account",
        "hero_eyebrow": "Fast. Secure. Traceable.",
        "video_preview_label": "Campus payment preview",
        "slide_title_1": "Seamless Checkout",
        "slide_text_1": "Simple form flow with instant confirmation.",
        "slide_title_2": "Proof in Seconds",
        "slide_text_2": "Every transaction gets a printable receipt.",
        "slide_title_3": "Secure Payments",
        "slide_text_3": "Protected payment flow for fast and reliable transactions.",
        "landing_student_portal_title": "Student Portal",
        "landing_student_portal_text": "Register, login, and pay your fees with MTN MoMo or Orange Money.",
        "landing_open_student_portal": "Open Student Portal",
        "landing_support_title": "Support Center",
        "landing_support_text": "Need help? Contact the school finance team for payment guidance and issue resolution.",
        "landing_receipt_title": "Instant Receipt",
        "landing_receipt_text": "Get a unique transaction ID and printable receipt after payment.",
        "student_dashboard_welcome": "Welcome,",
        "student_dashboard_subtitle": "Track your profile and payment activity in one place.",
        "student_dashboard_your_details": "Your Details",
        "student_dashboard_matricule": "Matricule",
        "student_dashboard_specialty": "Department",
        "student_dashboard_department": "Department",
        "student_dashboard_level_program": "Level / Program",
        "student_dashboard_phone": "Phone",
        "student_dashboard_change_password": "Change Password",
        "student_change_password_title": "Change Password",
        "student_change_password_subtitle": "Enter your current password and choose a new one.",
        "student_change_password_old": "Current Password",
        "student_change_password_new": "New Password",
        "student_change_password_confirm": "Confirm New Password",
        "student_change_password_policy": "Use at least 9 characters with 1 uppercase, 1 number, and 1 special character.",
        "student_change_password_submit": "Update Password",
        "student_dashboard_payment_code": "Registration Code",
        "student_dashboard_academic_year": "Academic Year",
        "student_dashboard_fee_total": "Annual Fee",
        "student_dashboard_fee_balance": "Outstanding Balance",
        "student_fee_paid": "Paid",
        "student_dashboard_installments": "Fee Summary",
        "student_dashboard_not_available": "Not available",
        "student_dashboard_make_payment": "Make a Payment",
        "student_dashboard_make_payment_text": "Pay your school fees with MTN MoMo or Orange Money and get an instant receipt.",
        "student_dashboard_pay_now": "Pay Now",
        "student_dashboard_payment_history": "Payment History",
        "student_dashboard_transaction_id": "Transaction ID",
        "student_dashboard_amount": "Amount",
        "student_dashboard_purpose": "Purpose",
        "student_dashboard_status": "Status",
        "student_dashboard_date": "Date",
        "student_dashboard_receipt": "Receipt",
        "student_dashboard_view": "View",
        "student_dashboard_no_payments": "No payments yet.",
        "student_dashboard_receipts": "Receipts",
        "student_dashboard_delete_receipt": "Delete receipt",
        "student_dashboard_delete_receipt_confirm": "Delete this receipt? This cannot be undone.",
        "student_dashboard_receipt_card_title": "Receipt",
        "student_dashboard_open_receipt": "Open Receipt",
        "student_dashboard_no_receipts": "No Receipts Yet",
        "student_dashboard_no_receipts_text": "Complete a payment to see printable receipts here.",
        "student_pay_title": "School Fee Payment",
        "student_pay_subtitle": "Review your fee details and complete your payment.",
        "student_pay_registration_code": "Registration Code",
        "student_pay_load_info": "Load My Info",
        "student_pay_full_name": "Full Name",
        "student_pay_dob": "Date of Birth",
        "student_pay_phone_mtn": "Mobile Money Number",
        "student_pay_specialty": "Department / Program",
        "student_pay_matricule": "Matricule",
        "student_pay_level_program": "Level / Program",
        "student_pay_purpose": "Purpose of Payment",
        "student_pay_purpose_value": "School Fees",
        "student_pay_amount": "Amount",
        "student_pay_installment": "Select Installment",
        "student_pay_installment_placeholder": "Choose installment",
        "student_pay_academic_year": "Academic Year",
        "student_pay_balance": "Outstanding Balance",
        "student_pay_minimum_hint": "Minimum payment is 50 frs.",
        "student_pay_mtn_phone": "Mobile Money Number",
        "student_pay_mtn_phone_placeholder": "e.g. 678905467 or +237678905467",
        "student_pay_method": "Payment Method",
        "student_pay_method_placeholder": "Select method",
        "student_pay_method_mtn": "MTN MoMo",
        "student_pay_method_orange": "Orange Money",
        "student_pay_pin": "5-digit PIN",
        "student_pay_pin_placeholder": "Enter 5-digit PIN",
        "student_pay_proceed": "Proceed to Payment",
        "receipt_title": "School Receipt",
        "receipt_date": "Date",
        "receipt_number": "Receipt No",
        "receipt_received_from": "Received from",
        "receipt_payment_date": "Payment Date",
        "receipt_description": "Description",
        "receipt_amount_xaf": "Amount (XAF)",
        "receipt_school_fee": "School Fee",
        "receipt_payment_method": "Payment Method",
        "receipt_payment_method_value": "Mobile Money",
        "receipt_status": "Status",
        "receipt_confirmation_code": "Confirmation Code",
        "receipt_matricule": "Matricule",
        "receipt_academic_year": "Academic Year",
        "receipt_installment": "Installment",
        "receipt_fee_total": "Annual Fee",
        "receipt_balance_after": "Balance After Payment",
        "receipt_hint": "Thank you for your payment. For any issue, contact school finance office.",
        "receipt_paid_stamp": "PAID",
        "receipt_print": "Print Receipt",
        "receipt_back_dashboard": "Back to Dashboard",
        "payment_success_title": "Payment Successful",
        "payment_success_subtitle": "Your school fee payment has been recorded successfully.",
        "payment_success_school": "School",
        "payment_success_amount_paid": "Amount Paid",
        "payment_success_transaction_id": "Transaction ID",
        "payment_success_date": "Date",
        "payment_success_academic_year": "Academic Year",
        "payment_success_installment": "Installment",
        "payment_success_balance": "Outstanding Balance",
        "payment_success_show_receipt": "Show Receipt",
        "payment_success_open_print": "Open & Print Receipt",
        "payment_success_back_dashboard": "Back to Dashboard",
        "payment_pending_notice": "Payment submitted and pending admin approval. Receipt will be available once approved.",
        "payment_approved_notice": "Your payment has been approved. You can now view your receipt.",
        "payment_processing_notice": "Payment is processing. Check your dashboard later for receipt availability.",
        "payment_successful_status": "Payment Successful",
        "payment_processing_status": "Processing",
        "payment_paid_status": "Paid",
        "receipt_download": "Download",
        "receipt_pending_notice": "Receipt unavailable while payment is pending admin approval.",
        "receipt_void_notice": "Receipt unavailable because this payment was voided by the admin.",
        "receipt_waiting_badge": "Pending Approval",
        "receipt_void_badge": "Voided",
    },
    "fr": {
        "brand": "Portail des frais IUGET",
        "home": "Accueil",
        "student_portal": "Portail Étudiant",
        "make_payment": "Paiement",
        "admin_portal": "Portail Admin",
        "payments": "Paiements",
        "students": "Étudiants",
        "logout": "Déconnexion",
        "login": "Connexion",
        "register": "Inscription",
        "welcome_back": "Bon retour",
        "sign_in_subtitle": "Connectez-vous à votre compte de paiement des frais scolaires.",
        "email_or_matricule": "Email ou Matricule",
        "password": "Mot de passe",
        "sign_in": "Se connecter",
        "create_account": "Créer un compte étudiant",
        "register_subtitle": "Remplissez vos informations pour payer vos frais scolaires en ligne.",
        "full_name": "Nom complet",
        "date_of_birth": "Date de naissance",
        "specialty": "Filière / Département",
        "level_or_program": "Niveau ou Programme",
        "phone_mtn": "Numéro de téléphone (MTN)",
        "phone_number": "Numéro de téléphone",
        "school_name": "Nom de l'école",
        "matricule": "Matricule",
        "email": "Email",
        "create_account_btn": "Créer le compte",
        "pay_confidence": "Payez vos frais scolaires en toute confiance",
        "lead_text": "Un portail professionnel permettant aux étudiants de payer leurs frais scolaires via MTN MoMo ou Orange Money et d'obtenir un reçu instantané.",
        "create_student_account": "Créer un compte étudiant",
        "hero_eyebrow": "Rapide. Sécurisé. Traçable.",
        "video_preview_label": "Aperçu du paiement scolaire",
        "slide_title_1": "Paiement fluide",
        "slide_text_1": "Un parcours simple avec confirmation instantanée.",
        "slide_title_2": "Preuve immédiate",
        "slide_text_2": "Chaque transaction génère un reçu imprimable.",
        "slide_title_3": "Paiements sécurisés",
        "slide_text_3": "Flux de paiement protégé pour des transactions rapides et fiables.",
        "landing_student_portal_title": "Portail Étudiant",
        "landing_student_portal_text": "Inscrivez-vous, connectez-vous et payez vos frais via MTN MoMo ou Orange Money.",
        "landing_open_student_portal": "Ouvrir le Portail Étudiant",
        "landing_support_title": "Centre d'assistance",
        "landing_support_text": "Besoin d'aide ? Contactez l'équipe financière de l'école pour l'assistance de paiement.",
        "landing_receipt_title": "Reçu Instantané",
        "landing_receipt_text": "Obtenez un identifiant de transaction unique et un reçu imprimable après paiement.",
        "student_dashboard_welcome": "Bienvenue,",
        "student_dashboard_subtitle": "Suivez votre profil et vos paiements au même endroit.",
        "student_dashboard_your_details": "Vos informations",
        "student_dashboard_matricule": "Matricule",
        "student_dashboard_specialty": "Département",
        "student_dashboard_department": "Département",
        "student_dashboard_level_program": "Niveau / Programme",
        "student_dashboard_phone": "Téléphone",
        "student_dashboard_change_password": "Changer le mot de passe",
        "student_change_password_title": "Changer le mot de passe",
        "student_change_password_subtitle": "Entrez votre mot de passe actuel et choisissez-en un nouveau.",
        "student_change_password_old": "Mot de passe actuel",
        "student_change_password_new": "Nouveau mot de passe",
        "student_change_password_confirm": "Confirmer le nouveau mot de passe",
        "student_change_password_policy": "Utilisez au moins 9 caractères avec 1 majuscule, 1 chiffre et 1 caractère spécial.",
        "student_change_password_submit": "Mettre à jour le mot de passe",
        "student_dashboard_payment_code": "Code d'inscription",
        "student_dashboard_academic_year": "Année académique",
        "student_dashboard_fee_total": "Frais annuels",
        "student_dashboard_fee_balance": "Solde restant",
        "student_fee_paid": "Payé",
        "student_dashboard_installments": "Résumé des frais",
        "student_dashboard_not_available": "Non disponible",
        "student_dashboard_make_payment": "Effectuer un paiement",
        "student_dashboard_make_payment_text": "Payez vos frais via MTN MoMo ou Orange Money et obtenez un reçu instantané.",
        "student_dashboard_pay_now": "Payer maintenant",
        "student_dashboard_payment_history": "Historique des paiements",
        "student_dashboard_transaction_id": "ID Transaction",
        "student_dashboard_amount": "Montant",
        "student_dashboard_purpose": "Objet",
        "student_dashboard_status": "Statut",
        "student_dashboard_date": "Date",
        "student_dashboard_receipt": "Reçu",
        "student_dashboard_view": "Voir",
        "student_dashboard_no_payments": "Aucun paiement pour le moment.",
        "student_dashboard_receipts": "Reçus",
        "student_dashboard_delete_receipt": "Supprimer le reçu",
        "student_dashboard_delete_receipt_confirm": "Supprimer ce reçu ? Cette action est irréversible.",
        "student_dashboard_receipt_card_title": "Reçu",
        "student_dashboard_open_receipt": "Ouvrir le reçu",
        "student_dashboard_no_receipts": "Aucun reçu",
        "student_dashboard_no_receipts_text": "Effectuez un paiement pour voir les reçus imprimables ici.",
        "student_pay_title": "Paiement des frais scolaires",
        "student_pay_subtitle": "Consultez vos frais puis finalisez le paiement.",
        "student_pay_registration_code": "Code d'inscription",
        "student_pay_load_info": "Charger mes infos",
        "student_pay_full_name": "Nom complet",
        "student_pay_dob": "Date de naissance",
        "student_pay_phone_mtn": "Numéro Mobile Money",
        "student_pay_specialty": "Département / Filière",
        "student_pay_matricule": "Matricule",
        "student_pay_level_program": "Niveau / Programme",
        "student_pay_purpose": "Motif du paiement",
        "student_pay_purpose_value": "Frais scolaires",
        "student_pay_amount": "Montant",
        "student_pay_installment": "Choisir la tranche",
        "student_pay_installment_placeholder": "Sélectionner la tranche",
        "student_pay_academic_year": "Année académique",
        "student_pay_balance": "Solde restant",
        "student_pay_minimum_hint": "Le paiement minimum est de 50 frs.",
        "student_pay_mtn_phone": "Numéro Mobile Money",
        "student_pay_mtn_phone_placeholder": "ex: 678905467 ou +237678905467",
        "student_pay_method": "Mode de paiement",
        "student_pay_method_placeholder": "Choisir un mode",
        "student_pay_method_mtn": "MTN MoMo",
        "student_pay_method_orange": "Orange Money",
        "student_pay_pin": "PIN à 5 chiffres",
        "student_pay_pin_placeholder": "Entrez le PIN à 5 chiffres",
        "student_pay_proceed": "Continuer vers le paiement",
        "receipt_title": "Reçu scolaire",
        "receipt_date": "Date",
        "receipt_number": "N° Reçu",
        "receipt_received_from": "Reçu de",
        "receipt_payment_date": "Date de paiement",
        "receipt_description": "Description",
        "receipt_amount_xaf": "Montant (XAF)",
        "receipt_school_fee": "Frais scolaires",
        "receipt_payment_method": "Mode de paiement",
        "receipt_payment_method_value": "Mobile Money",
        "receipt_status": "Statut",
        "receipt_confirmation_code": "Code de confirmation",
        "receipt_matricule": "Matricule",
        "receipt_academic_year": "Année académique",
        "receipt_installment": "Tranche",
        "receipt_fee_total": "Frais annuels",
        "receipt_balance_after": "Solde après paiement",
        "receipt_hint": "Merci pour votre paiement. Pour tout problème, contactez le service financier.",
        "receipt_paid_stamp": "PAYE",
        "receipt_print": "Imprimer le reçu",
        "receipt_back_dashboard": "Retour au tableau de bord",
        "payment_success_title": "Paiement réussi",
        "payment_success_subtitle": "Votre paiement des frais scolaires a été enregistré avec succès.",
        "payment_success_school": "École",
        "payment_success_amount_paid": "Montant payé",
        "payment_success_transaction_id": "ID Transaction",
        "payment_success_date": "Date",
        "payment_success_academic_year": "Année académique",
        "payment_success_installment": "Tranche",
        "payment_success_balance": "Solde restant",
        "payment_success_show_receipt": "Afficher le reçu",
        "payment_success_open_print": "Ouvrir et imprimer le reçu",
        "payment_success_back_dashboard": "Retour au tableau de bord",
        "payment_pending_notice": "Paiement soumis et en attente d'approbation. Le reçu sera disponible après validation.",
        "payment_approved_notice": "Votre paiement a été approuvé. Vous pouvez maintenant afficher le reçu.",
        "payment_processing_notice": "Paiement en cours de traitement. Consultez votre tableau de bord plus tard pour le reçu.",
        "payment_successful_status": "Paiement réussi",
        "payment_processing_status": "En traitement",
        "payment_paid_status": "Payé",
        "receipt_download": "Télécharger",
        "receipt_pending_notice": "Reçu indisponible tant que le paiement est en attente d'approbation.",
        "receipt_void_notice": "Reçu indisponible car le paiement a été annulé par l'admin.",
        "receipt_waiting_badge": "En attente de validation",
        "receipt_void_badge": "Annulé",
    },
}


def current_academic_year(today: date | None = None) -> str:
    current = today or date.today()
    if current.month >= 9:
        return f"{current.year}/{current.year + 1}"
    return f"{current.year - 1}/{current.year}"


def build_installments(total_amount: int) -> list[int]:
    raw_amounts = [int(round(total_amount * ratio)) for ratio in DEFAULT_INSTALLMENT_SPLIT]
    diff = total_amount - sum(raw_amounts)
    if raw_amounts:
        raw_amounts[-1] += diff
    return raw_amounts

app = Flask(__name__)
app.secret_key = APP_SECRET

DEFAULT_STUDENT_COL_MAP = {
    "name": "full_name",
    "specialty": "specialty",
    "program_level": "program_level",
    "matricule": "matricule",
    "phone": "phone",
    "dob": "dob",
    "email": "email",
    "password": "password_hash",
    "access_code": "access_code",
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def ensure_contact_messages_schema():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS contact_messages ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "full_name VARCHAR(150) NOT NULL, "
            "email VARCHAR(191) NOT NULL, "
            "subject VARCHAR(200) NOT NULL, "
            "message TEXT NOT NULL, "
            "overall_satisfaction TINYINT NULL, "
            "status VARCHAR(20) NOT NULL DEFAULT 'Open', "
            "admin_reply TEXT NULL, "
            "replied_by VARCHAR(150) NULL, "
            "replied_at DATETIME NULL, "
            "sender_ip VARCHAR(45) NULL, "
            "admin_seen TINYINT(1) NOT NULL DEFAULT 0, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        cur.execute("SHOW COLUMNS FROM contact_messages")
        cols = {row[0] for row in cur.fetchall()}
        if "status" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'Open'")
        if "admin_reply" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN admin_reply TEXT NULL")
        if "replied_by" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN replied_by VARCHAR(150) NULL")
        if "replied_at" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN replied_at DATETIME NULL")
        if "sender_ip" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN sender_ip VARCHAR(45) NULL")
        if "admin_seen" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN admin_seen TINYINT(1) NOT NULL DEFAULT 0")
        if "overall_satisfaction" not in cols:
            cur.execute("ALTER TABLE contact_messages ADD COLUMN overall_satisfaction TINYINT NULL")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_password_reset_tokens_schema():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS password_reset_tokens ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "student_id INT NOT NULL, "
            "token VARCHAR(80) NOT NULL, "
            "expires_at DATETIME NOT NULL, "
            "used TINYINT(1) NOT NULL DEFAULT 0, "
            "used_at DATETIME NULL, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
            "UNIQUE KEY uq_password_reset_token (token), "
            "KEY idx_password_reset_student_id (student_id), "
            "CONSTRAINT fk_password_reset_student "
            "FOREIGN KEY (student_id) REFERENCES students(id) "
            "ON DELETE CASCADE ON UPDATE CASCADE"
            ")"
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_payments_schema():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SHOW COLUMNS FROM payments")
        cols = {row[0] for row in cur.fetchall()}
        if "approved_at" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN approved_at DATETIME NULL")
        if "approved_by" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN approved_by VARCHAR(150) NULL")
        if "student_seen" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN student_seen TINYINT(1) NOT NULL DEFAULT 0")
        if "payment_method" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN payment_method VARCHAR(40) NULL")
        if "academic_year" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN academic_year VARCHAR(20) NULL")
        if "installment_label" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN installment_label VARCHAR(40) NULL")
        if "fee_total" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN fee_total DECIMAL(12,2) NULL")
        if "balance_after" not in cols:
            cur.execute("ALTER TABLE payments ADD COLUMN balance_after DECIMAL(12,2) NULL")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_departments_schema():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS departments ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "name VARCHAR(120) NOT NULL UNIQUE, "
            "code VARCHAR(20) NULL, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        cur.execute("SHOW COLUMNS FROM departments")
        cols = {row[0] for row in cur.fetchall()}
        if "code" not in cols:
            cur.execute("ALTER TABLE departments ADD COLUMN code VARCHAR(20) NULL")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_fee_items_schema():
    ensure_departments_schema()
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS fee_items ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "department_id INT NOT NULL, "
            "program_level VARCHAR(40) NOT NULL, "
            "fee_type VARCHAR(60) NOT NULL, "
            "total_fee DECIMAL(12,2) NOT NULL, "
            "installment1 DECIMAL(12,2) NULL, "
            "installment2 DECIMAL(12,2) NULL, "
            "installment3 DECIMAL(12,2) NULL, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, "
            "KEY idx_fee_items_dept_level (department_id, program_level), "
            "CONSTRAINT fk_fee_items_department "
            "FOREIGN KEY (department_id) REFERENCES departments(id) "
            "ON DELETE CASCADE ON UPDATE CASCADE"
            ")"
        )
        cur.execute("SHOW COLUMNS FROM fee_items")
        cols = {row[0] for row in cur.fetchall()}
        if "fee_type" not in cols:
            cur.execute("ALTER TABLE fee_items ADD COLUMN fee_type VARCHAR(60) NOT NULL DEFAULT 'Tuition'")
        if "total_fee" not in cols:
            cur.execute("ALTER TABLE fee_items ADD COLUMN total_fee DECIMAL(12,2) NOT NULL DEFAULT 0")
        if "installment1" not in cols:
            cur.execute("ALTER TABLE fee_items ADD COLUMN installment1 DECIMAL(12,2) NULL")
        if "installment2" not in cols:
            cur.execute("ALTER TABLE fee_items ADD COLUMN installment2 DECIMAL(12,2) NULL")
        if "installment3" not in cols:
            cur.execute("ALTER TABLE fee_items ADD COLUMN installment3 DECIMAL(12,2) NULL")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_students_fee_columns():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SHOW COLUMNS FROM students")
        cols = {row[0] for row in cur.fetchall()}
        if "fee_total" not in cols:
            cur.execute("ALTER TABLE students ADD COLUMN fee_total DECIMAL(12,2) NULL")
        if "paid_amount" not in cols:
            cur.execute("ALTER TABLE students ADD COLUMN paid_amount DECIMAL(12,2) NOT NULL DEFAULT 0")
        if "balance_amount" not in cols:
            cur.execute("ALTER TABLE students ADD COLUMN balance_amount DECIMAL(12,2) NULL")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def ensure_school_finance_schema():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS school_finance ("
            "id INT PRIMARY KEY, "
            "total_collected DECIMAL(14,2) NOT NULL DEFAULT 0, "
            "updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ")"
        )
        cur.execute("SELECT id FROM school_finance WHERE id = 1")
        if not cur.fetchone():
            cur.execute("INSERT INTO school_finance (id, total_collected) VALUES (1, 0)")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_departments() -> list[str]:
    try:
        ensure_departments_schema()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM departments ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except MySQLError:
        return []


def fetch_fee_items(department: str, program_level: str) -> list[dict]:
    if not department:
        return []
    try:
        ensure_fee_items_schema()
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT fi.fee_type, fi.total_fee, fi.installment1, fi.installment2, fi.installment3 "
            "FROM fee_items fi JOIN departments d ON fi.department_id = d.id "
            "WHERE d.name = %s AND fi.program_level = %s "
            "ORDER BY fi.id",
            (department, program_level),
        )
        rows = cur.fetchall() or []
        if not rows:
            cur.execute(
                "SELECT fi.fee_type, fi.total_fee, fi.installment1, fi.installment2, fi.installment3 "
                "FROM fee_items fi JOIN departments d ON fi.department_id = d.id "
                "WHERE d.name = %s AND fi.program_level = %s "
                "ORDER BY fi.id",
                (department, "ALL"),
            )
            rows = cur.fetchall() or []
        cur.close()
        conn.close()
        return rows
    except MySQLError:
        return []


def recalculate_student_finance(student_id: int, fee_total: float) -> dict:
    ensure_students_fee_columns()
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT IFNULL(SUM(amount), 0) AS paid_sum FROM payments WHERE student_id = %s AND status = 'Paid'",
        (student_id,),
    )
    row = cur.fetchone() or {}
    paid_sum = float(row.get("paid_sum") or 0)
    balance = max(fee_total - paid_sum, 0.0)
    cur.execute(
        "UPDATE students SET fee_total = %s, paid_amount = %s, balance_amount = %s WHERE id = %s",
        (fee_total, paid_sum, balance, student_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"fee_total": fee_total, "paid_amount": paid_sum, "balance": balance}


def sync_student_fee(student_id: int, department: str, program_level: str) -> dict:
    items = fetch_fee_items(department, program_level)
    if items:
        fee_total = sum(float(item.get("total_fee") or 0) for item in items)
    else:
        fee_total = float(DEFAULT_YEARLY_FEE_XAF)
    return recalculate_student_finance(student_id, fee_total)


def get_installment_plan(department: str, program_level: str, fee_total: float) -> list[dict]:
    items = fetch_fee_items(department, program_level)
    installments = None
    if items:
        sums = [0.0, 0.0, 0.0]
        for item in items:
            sums[0] += float(item.get("installment1") or 0)
            sums[1] += float(item.get("installment2") or 0)
            sums[2] += float(item.get("installment3") or 0)
        if any(sums):
            installments = sums
    if not installments:
        installments = [float(v) for v in build_installments(int(round(fee_total)))]
    labels = ["1st", "2nd", "3rd"]
    plan = []
    for idx, amount in enumerate(installments[:3]):
        plan.append({"label": labels[idx], "amount": float(amount)})
    return plan


def apply_installments_to_amount(installments: list[dict], paid_total: float) -> list[dict]:
    remaining = paid_total
    applied = []
    for item in installments:
        amount = float(item["amount"])
        paid_here = min(max(remaining, 0.0), amount)
        remaining -= paid_here
        status = "Paid" if paid_here >= amount and amount > 0 else ("Partial" if paid_here > 0 else "Unpaid")
        applied.append(
            {
                "label": item["label"],
                "amount": amount,
                "paid": paid_here,
                "remaining": max(amount - paid_here, 0.0),
                "status": status,
            }
        )
    return applied


def build_fee_breakdown(department: str, program_level: str, paid_total: float) -> list[dict]:
    items = fetch_fee_items(department, program_level)
    breakdown = []
    remaining_paid = float(paid_total or 0)
    if not items:
        return breakdown
    for item in items:
        total_fee = float(item.get("total_fee") or 0)
        insts = [
            float(item.get("installment1") or 0),
            float(item.get("installment2") or 0),
            float(item.get("installment3") or 0),
        ]
        if not any(insts):
            insts = [float(v) for v in build_installments(int(round(total_fee)))]
        paid_for_item = min(remaining_paid, total_fee)
        remaining_paid = max(remaining_paid - paid_for_item, 0.0)
        inst_plan = [
            {"label": "1st", "amount": insts[0]},
            {"label": "2nd", "amount": insts[1]},
            {"label": "3rd", "amount": insts[2]},
        ]
        inst_applied = apply_installments_to_amount(inst_plan, paid_for_item)
        status = "Completed" if total_fee > 0 and paid_for_item >= total_fee else ("Partial" if paid_for_item > 0 else "Not Paid")
        breakdown.append(
            {
                "fee_type": item.get("fee_type") or "Tuition",
                "total_fee": total_fee,
                "installments": inst_applied,
                "status": status,
            }
        )
    return breakdown


def increment_school_total(amount: float) -> None:
    ensure_school_finance_schema()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE school_finance SET total_collected = total_collected + %s WHERE id = 1",
        (amount,),
    )
    conn.commit()
    cur.close()
    conn.close()


def fetch_school_total_collected(retries: int = 2, delay: float = 0.2) -> float:
    ensure_school_finance_schema()
    for attempt in range(retries + 1):
        conn = None
        cur = None
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT total_collected FROM school_finance WHERE id = 1")
            row = cur.fetchone()
            return float(row[0]) if row else 0.0
        except MySQLError as exc:
            err_no = getattr(exc, "errno", None)
            if err_no == 1412 or "Table definition has changed" in str(exc):
                if attempt < retries:
                    time.sleep(delay)
                    continue
            return 0.0
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


def ensure_admin_audit_schema():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS admin_audit_log ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "admin_id INT NULL, "
            "admin_name VARCHAR(150) NULL, "
            "action VARCHAR(50) NOT NULL, "
            "entity_type VARCHAR(50) NOT NULL, "
            "entity_id VARCHAR(64) NOT NULL, "
            "details TEXT NULL, "
            "created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def log_admin_action(action: str, entity_type: str, entity_id: str, details: str | None = None) -> None:
    try:
        ensure_admin_audit_schema()
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO admin_audit_log (admin_id, admin_name, action, entity_type, entity_id, details) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                session.get("user_id"),
                session.get("name"),
                action,
                entity_type,
                entity_id,
                details,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except MySQLError:
        pass


def contains_html_or_script(value: str) -> bool:
    if not value:
        return False
    lower = value.lower()
    if re.search(r"<[^>]+>", value):
        return True
    blocked_tokens = ("javascript:", "<script", "</script", "onerror=", "onload=", "<iframe", "</iframe")
    return any(token in lower for token in blocked_tokens)


def should_flag_for_moderation(value: str) -> bool:
    if not value:
        return False
    lower = value.lower()
    urls = re.findall(r"https?://|www\.", lower)
    return len(urls) >= 2


@app.context_processor
def inject_globals():
    lang = resolve_language()

    def t(key: str) -> str:
        return TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key) or key

    new_contact_alerts = 0
    if session.get("role") == "admin":
        try:
            ensure_contact_messages_schema()
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM contact_messages WHERE admin_seen = 0")
            row = cur.fetchone()
            new_contact_alerts = int((row[0] if row else 0) or 0)
            cur.close()
            conn.close()
        except MySQLError:
            new_contact_alerts = 0

    return {
        "school_name": APP_SCHOOL_NAME,
        "current_lang": lang,
        "t": t,
        "new_contact_alerts": new_contact_alerts,
        "course_options": get_departments() or COURSE_OPTIONS,
    }


def translate(key: str) -> str:
    lang = resolve_language()
    return TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key) or key


def resolve_language() -> str:
    lang = (session.get("lang") or "").strip().lower()
    if not lang:
        lang = (request.cookies.get("lang") or "").strip().lower()
    if not lang:
        lang = (request.args.get("lang") or "").strip().lower()
    if not lang:
        accept = request.headers.get("Accept-Language", "")
        if accept:
            lang = accept.split(",")[0].strip().lower()[:2]
    if lang not in SUPPORTED_LANGS:
        lang = "en"
    return lang


@app.before_request
def sync_language_preference():
    lang = (request.args.get("lang") or "").strip().lower()
    if lang in SUPPORTED_LANGS:
        session["lang"] = lang
        return
    cookie_lang = (request.cookies.get("lang") or "").strip().lower()
    if cookie_lang in SUPPORTED_LANGS and session.get("lang") != cookie_lang:
        session["lang"] = cookie_lang


def set_banner(message: str, level: str = "info") -> None:
    session["banner_message"] = message
    session["banner_level"] = level


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code in SUPPORTED_LANGS:
        session["lang"] = lang_code
    next_url = request.args.get("next") or url_for("index")
    resp = redirect(next_url)
    if lang_code in SUPPORTED_LANGS:
        resp.set_cookie("lang", lang_code, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return resp


def get_table_columns(table_name: str) -> set[str]:
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(f"SHOW COLUMNS FROM {table_name}")
        return {row[0] for row in cur.fetchall()}
    except mysql.connector.Error:
        return set()
    finally:
        cur.close()
        conn.close()


def students_has_email_column() -> bool:
    cols = get_table_columns("students")
    return ("email" in cols) or (not cols)


def student_column_map() -> dict:
    cols = get_table_columns("students")

    def pick(*names):
        for name in names:
            if name in cols:
                return name
        return None

    mapped = {
        "name": pick("full_name", "student_name", "name", "fullname"),
        "specialty": pick("specialty", "department", "program"),
        "program_level": pick("program_level", "academic_level", "level", "class"),
        "matricule": pick("matricule", "student_id"),
        "phone": pick("phone", "phone_number", "tel"),
        "dob": pick("dob", "date_of_birth", "birth_date"),
        "email": pick("email", "mail"),
        "password": pick("password_hash", "password", "passwd", "pass_word", "pwd"),
        "access_code": pick("access_code", "payment_code", "auth_code", "reg_code"),
    }

    # If schema introspection fails, fall back to the known project schema.
    if not cols:
        return DEFAULT_STUDENT_COL_MAP.copy()

    # If some columns are missing from aliases, use standard project names when present.
    for key, default_col in DEFAULT_STUDENT_COL_MAP.items():
        if mapped.get(key) is None and default_col in cols:
            mapped[key] = default_col

    return mapped


def student_select_expr(alias: str, column_name: str | None, default_value: str = "") -> str:
    if column_name:
        return f"s.{column_name} AS {alias}"
    return f"'{default_value}' AS {alias}"


def password_matches(stored_password: str | None, provided_password: str) -> bool:
    if not stored_password:
        return False
    # Hashed formats used by Werkzeug usually have an algorithm prefix.
    if ":" in stored_password or "$" in stored_password:
        try:
            return check_password_hash(stored_password, provided_password)
        except ValueError:
            return stored_password == provided_password
    return stored_password == provided_password


def validate_password_policy(password: str) -> tuple[bool, str]:
    if len(password) < 9:
        return False, "Password must be at least 9 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Password must include at least one special character."
    return True, ""


def generate_password_reset_token() -> str:
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    specials = "!@#$%^&*?"
    # Easier-to-type format while still enforcing uppercase + numbers + special char.
    return (
        f"{secrets.choice(uppercase)}{secrets.choice(uppercase)}{secrets.choice(uppercase)}"
        f"{secrets.choice(digits)}{secrets.choice(digits)}{secrets.choice(digits)}"
        f"{secrets.choice(specials)}"
    )


def generate_access_code() -> str:
    return str(random.randint(100000, 999999))


def generate_temp_password(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*?"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def student_profile_data(student: dict, student_cols: dict, fallback_name: str = "Student") -> dict:
    def pick(key: str, default: str = ""):
        col = student_cols.get(key)
        if col and student and student.get(col) not in (None, ""):
            return student.get(col)
        if student and student.get(key) not in (None, ""):
            return student.get(key)
        return default

    dob_value = pick("dob", "")
    if hasattr(dob_value, "strftime"):
        dob_value = dob_value.strftime("%Y-%m-%d")
    elif dob_value:
        dob_value = str(dob_value)

    return {
        "full_name": pick("name", fallback_name),
        "dob": dob_value,
        "phone": str(pick("phone", "")),
        "specialty": str(pick("specialty", "")),
        "program_level": str(pick("program_level", "")),
        "matricule": str(pick("matricule", "undefined")),
        "access_code": str(pick("access_code", "")),
    }


def normalize_cm_number(phone: str) -> str:
    if not phone:
        return ""
    digits = "".join([c for c in phone if c.isdigit()])

    # Cameroon handling:
    # accepted formats -> 678905467, 0678905467, 237678905467, +237678905467
    if digits.startswith("237") and len(digits) == 12:
        return digits[3:]
    if digits.startswith("0") and len(digits) == 10:
        return digits[1:]
    if len(digits) == 9:
        return digits
    return ""


def is_cm_number(phone: str) -> bool:
    return bool(normalize_cm_number(phone))


def is_mtn_number(phone: str) -> bool:
    cm_local = normalize_cm_number(phone)
    if cm_local and cm_local[:3] in MTN_CAMEROON_PREFIXES:
        return True
    return False


def is_orange_number(phone: str) -> bool:
    cm_local = normalize_cm_number(phone)
    if cm_local and cm_local[:3] in ORANGE_CAMEROON_PREFIXES:
        return True
    return False


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in first.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have access to that page.", "error")
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def smtp_enabled() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS and SMTP_SENDER)


def send_smtp_email(to_email, subject, html_content, text_content=None):
    if not smtp_enabled():
        return False, "SMTP is not configured."

    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = SMTP_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        if text_content:
            msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)


def send_registration_email(user_email, display_name, reg_code):
    if not smtp_enabled() or not user_email:
        return False, "Registration email is not configured."

    safe_name = html.escape(display_name or "Student")
    safe_email = html.escape(user_email)
    safe_code = html.escape(reg_code or "")

    subject = f"Welcome to {APP_SCHOOL_NAME}"
    html_body = (
        f"<h3>Registration Successful</h3>"
        f"<p>Hi {safe_name}, your account has been created on {html.escape(APP_SCHOOL_NAME)}.</p>"
        f"<p><strong>Email:</strong> {safe_email}</p>"
        f"<p><strong>Payment Code:</strong> {safe_code}</p>"
        f"<p>You can now log in and complete your school fee payment.</p>"
    )
    text_body = (
        "Registration Successful\n"
        f"Hi {display_name or 'Student'}, your account has been created on {APP_SCHOOL_NAME}.\n"
        f"Email: {user_email}\n"
        f"Payment Code: {reg_code}\n"
        "You can now log in and complete your school fee payment.\n"
    )
    return send_smtp_email(
        to_email=user_email,
        subject=subject,
        html_content=html_body,
        text_content=text_body,
    )


def send_student_credentials_email(user_email: str, display_name: str, temp_password: str) -> tuple[bool, str]:
    if not smtp_enabled() or not user_email:
        return False, "Email delivery is not configured."

    safe_name = html.escape(display_name or "Student")
    safe_email = html.escape(user_email)
    safe_password = html.escape(temp_password)

    subject = f"Your {APP_SCHOOL_NAME} Student Login Details"
    html_body = (
        f"<h3>Student Account Created</h3>"
        f"<p>Hello {safe_name},</p>"
        f"<p>Your student account has been created for {html.escape(APP_SCHOOL_NAME)}.</p>"
        f"<p><strong>Login Email:</strong> {safe_email}<br>"
        f"<strong>Temporary Password:</strong> {safe_password}</p>"
        f"<p>Please log in and change your password after your first sign-in.</p>"
    )
    text_body = (
        f"Hello {display_name or 'Student'},\n"
        f"Your student account has been created for {APP_SCHOOL_NAME}.\n"
        f"Login Email: {user_email}\n"
        f"Temporary Password: {temp_password}\n"
        "Please log in and change your password after your first sign-in.\n"
    )
    return send_smtp_email(
        to_email=user_email,
        subject=subject,
        html_content=html_body,
        text_content=text_body,
    )


def build_receipt_qr_payload(payment: dict, receipt_url: str | None = None) -> str:
    if receipt_url:
        return receipt_url
    created_at = payment.get("created_at")
    date_label = created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, "strftime") else ""
    parts = [
        f"School: {APP_SCHOOL_NAME}",
        f"Student: {payment.get('full_name') or ''}",
        f"Matricule: {payment.get('matricule') or ''}",
        f"Department: {payment.get('specialty') or ''}",
        f"Level: {payment.get('program_level') or ''}",
        f"Transaction: {payment.get('transaction_id') or ''}",
        f"Amount: {payment.get('amount') or ''} FCFA",
        f"Date: {date_label}",
        f"Status: {payment.get('status') or ''}",
    ]
    return "\n".join([p for p in parts if p.strip()])


def generate_qr_data_uri(payload: str) -> str | None:
    if not payload:
        return None
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
        img = qrcode.make(payload, error_correction=ERROR_CORRECT_M)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form_data = {"full_name": "", "email": "", "subject": "", "message": ""}
    message_history = []

    ensure_contact_messages_schema()
    contact_email = ""
    if session.get("role") == "student" and session.get("user_id"):
        form_data["full_name"] = session.get("name", "")
        try:
            conn_student = get_db()
            cur_student = conn_student.cursor(dictionary=True)
            student_cols = student_column_map()
            email_col = student_cols.get("email")
            if email_col:
                cur_student.execute(f"SELECT {email_col} AS email FROM students WHERE id = %s", (session["user_id"],))
                row = cur_student.fetchone()
                if row and row.get("email"):
                    contact_email = str(row.get("email")).strip().lower()
            cur_student.close()
            conn_student.close()
        except MySQLError:
            pass

    contact_email = (contact_email or "").strip().lower()
    if contact_email:
        form_data["email"] = contact_email
        try:
            conn_history = get_db()
            cur_history = conn_history.cursor(dictionary=True)
            cur_history.execute(
                "SELECT id, subject, message, status, admin_reply, replied_by, replied_at, created_at "
                "FROM contact_messages WHERE email = %s ORDER BY created_at DESC",
                (contact_email,),
            )
            message_history = cur_history.fetchall()
            cur_history.close()
            conn_history.close()
        except MySQLError:
            message_history = []

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        sender_ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()

        form_data = {
            "full_name": full_name,
            "email": email,
            "subject": subject,
            "message": message,
        }

        if not full_name or not email or not subject or not message:
            flash("All contact fields are required.", "error")
            return render_template("contact.html", form_data=form_data, message_history=message_history)

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid email address.", "error")
            return render_template("contact.html", form_data=form_data, message_history=message_history)

        if any(contains_html_or_script(v) for v in (full_name, subject, message)):
            flash("HTML or script content is not allowed in contact messages.", "error")
            return render_template("contact.html", form_data=form_data, message_history=message_history)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM contact_messages "
                "WHERE (email = %s OR (sender_ip IS NOT NULL AND sender_ip = %s)) "
                "AND created_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)",
                (email, sender_ip, CONTACT_RATE_WINDOW_MINUTES),
            )
            recent_count_row = cur.fetchone()
            recent_count = int((recent_count_row[0] if recent_count_row else 0) or 0)
            if recent_count >= CONTACT_RATE_MAX_MESSAGES:
                cur.close()
                conn.close()
                flash(
                    f"Too many messages sent recently. Please wait {CONTACT_RATE_WINDOW_MINUTES} minutes and try again.",
                    "error",
                )
                return render_template("contact.html", form_data=form_data, message_history=message_history)

            status = "Flagged" if should_flag_for_moderation(subject + " " + message) else "Open"
            cur.execute(
                "INSERT INTO contact_messages (full_name, email, subject, message, status, sender_ip, admin_seen) "
                "VALUES (%s, %s, %s, %s, %s, %s, 0)",
                (full_name, email, subject, message, status, sender_ip),
            )
            conn.commit()
            cur.close()
            conn.close()
        except MySQLError:
            flash("Failed to send message due to a database error.", "error")
            return render_template("contact.html", form_data=form_data, message_history=message_history)

        if status == "Flagged":
            flash("Your message was received and is pending admin review.", "warning")
        else:
            flash("Your message has been sent successfully.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html", form_data=form_data, message_history=message_history)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        flash("Student accounts are created by IUGET administration.", "warning")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = cur.fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            cur.close()
            conn.close()
            session["user_id"] = admin["id"]
            session["role"] = "admin"
            session["name"] = admin["full_name"]
            return redirect(url_for("admin_dashboard"))

        student_cols = student_column_map()
        email_col = student_cols["email"]
        if not email_col:
            cur.close()
            conn.close()
            flash("Students table is missing email column.", "error")
            return redirect(url_for("login"))
        cur.execute(f"SELECT * FROM students WHERE {email_col} = %s", (email,))
        student = cur.fetchone()
        cur.close()
        conn.close()

        password_col = student_cols["password"]
        stored_password = None
        if student:
            if password_col:
                stored_password = student.get(password_col)
            if not stored_password:
                stored_password = student.get("password_hash") or student.get("password")

        if student and password_matches(stored_password, password):
            display_name = (
                student.get(student_cols["name"]) if student_cols["name"] else None
            ) or student.get("matricule") or "Student"
            session["user_id"] = student["id"]
            session["role"] = "student"
            session["name"] = display_name
            return redirect(url_for("student_dashboard"))

        flash("Invalid credentials.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    reset_token = None
    entered_email = ""
    email_delivery_enabled = smtp_enabled()
    show_reset_token = False
    if request.method == "POST":
        entered_email = request.form.get("email", "").strip().lower()
        if not entered_email:
            flash("Email is required.", "error")
            return render_template(
                "forgot_password.html",
                entered_email=entered_email,
                reset_token=reset_token,
                show_reset_token=show_reset_token,
                email_delivery_enabled=email_delivery_enabled,
            )

        student_cols = student_column_map()
        email_col = student_cols.get("email")
        if not email_col:
            flash("Password reset is unavailable because email is not configured.", "error")
            return render_template(
                "forgot_password.html",
                entered_email=entered_email,
                reset_token=reset_token,
                show_reset_token=show_reset_token,
                email_delivery_enabled=email_delivery_enabled,
            )

        ensure_password_reset_tokens_schema()
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT id FROM students WHERE {email_col} = %s LIMIT 1", (entered_email,))
        student = cur.fetchone()
        if not student:
            cur.close()
            conn.close()
            flash("No account found for that email.", "error")
            return render_template(
                "forgot_password.html",
                entered_email=entered_email,
                reset_token=reset_token,
                show_reset_token=show_reset_token,
                email_delivery_enabled=email_delivery_enabled,
            )

        token = generate_password_reset_token()
        expires_at = datetime.now() + timedelta(minutes=15)
        for _ in range(5):
            try:
                cur.execute(
                    "INSERT INTO password_reset_tokens (student_id, token, expires_at, used) "
                    "VALUES (%s, %s, %s, 0)",
                    (student["id"], token, expires_at),
                )
                conn.commit()
                reset_token = token
                break
            except MySQLError:
                token = generate_password_reset_token()
        cur.close()
        conn.close()

        if not reset_token:
            flash("Could not generate a reset token. Please try again.", "error")
            return render_template(
                "forgot_password.html",
                entered_email=entered_email,
                reset_token=None,
                show_reset_token=show_reset_token,
                email_delivery_enabled=email_delivery_enabled,
            )

        if email_delivery_enabled:
            reset_url = f"{APP_BASE_URL}{url_for('reset_password')}"
            html_body = (
                f"<h3>Password Reset</h3>"
                f"<p>Your reset token is:</p>"
                f"<p><strong>{html.escape(reset_token)}</strong></p>"
                f"<p>Use it here: <a href=\"{html.escape(reset_url)}\">Reset Password</a></p>"
                f"<p>This token expires in 15 minutes.</p>"
            )
            text_body = (
                "Password Reset\n"
                f"Token: {reset_token}\n"
                f"Reset here: {reset_url}\n"
                "This token expires in 15 minutes.\n"
            )
            sent, err = send_smtp_email(
                to_email=entered_email,
                subject="Password reset token",
                html_content=html_body,
                text_content=text_body,
            )
            if sent:
                flash("Reset email sent. It will expire in 15 minutes.", "success")
            else:
                flash("Could not send reset email. Showing token here.", "error")
                show_reset_token = True
        else:
            flash("Reset token generated. It will expire in 15 minutes.", "success")
            show_reset_token = True

        reset_token = reset_token if show_reset_token else None
        if not show_reset_token:
            return redirect(url_for("reset_password"))

    return render_template(
        "forgot_password.html",
        entered_email=entered_email,
        reset_token=reset_token,
        show_reset_token=show_reset_token,
        email_delivery_enabled=email_delivery_enabled,
    )


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        new_password = request.form.get("new_password", "").strip()

        if not token or not new_password:
            flash("Token and new password are required.", "error")
            return render_template("reset_password.html")

        ok_password, password_msg = validate_password_policy(new_password)
        if not ok_password:
            flash(password_msg, "error")
            return render_template("reset_password.html")

        ensure_password_reset_tokens_schema()
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM password_reset_tokens WHERE token = %s ORDER BY id DESC LIMIT 1",
            (token,),
        )
        token_row = cur.fetchone()
        if not token_row:
            cur.close()
            conn.close()
            flash("Invalid reset token.", "error")
            return render_template("reset_password.html")

        if int(token_row.get("used", 0)) == 1:
            cur.close()
            conn.close()
            flash("This token has already been used.", "error")
            return render_template("reset_password.html")

        expires_at = token_row.get("expires_at")
        if not expires_at or expires_at < datetime.now():
            cur.close()
            conn.close()
            flash("This token has expired.", "error")
            return render_template("reset_password.html")

        student_cols = student_column_map()
        password_col = student_cols.get("password") or "password_hash"
        if not student_cols.get("password"):
            cols = get_table_columns("students")
            if "password_hash" not in cols:
                cur.execute("ALTER TABLE students ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''")
                conn.commit()

        cur.execute(
            f"UPDATE students SET {password_col} = %s WHERE id = %s",
            (generate_password_hash(new_password), token_row["student_id"]),
        )
        cur.execute(
            "UPDATE password_reset_tokens SET used = 1, used_at = %s WHERE id = %s",
            (datetime.now(), token_row["id"]),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Password successfully reset.", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html")


@app.route("/student/change-password", methods=["GET", "POST"])
@login_required(role="student")
def student_change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not old_password or not new_password or not confirm_password:
            flash("All password fields are required.", "error")
            return render_template("student_change_password.html")

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("student_change_password.html")

        ok_password, password_msg = validate_password_policy(new_password)
        if not ok_password:
            flash(password_msg, "error")
            return render_template("student_change_password.html")

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            student_cols = student_column_map()
            password_col = student_cols.get("password") or "password_hash"
            if not student_cols.get("password"):
                cols = get_table_columns("students")
                if "password_hash" not in cols:
                    cur.execute("ALTER TABLE students ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''")
                    conn.commit()

            cur.execute(
                f"SELECT {password_col} AS password_value FROM students WHERE id = %s",
                (session["user_id"],),
            )
            row = cur.fetchone()
            stored_password = row.get("password_value") if row else None
            if not stored_password or not password_matches(stored_password, old_password):
                flash("Current password is incorrect.", "error")
                return render_template("student_change_password.html")

            cur.execute(
                f"UPDATE students SET {password_col} = %s WHERE id = %s",
                (generate_password_hash(new_password), session["user_id"]),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

        flash("Password updated successfully.", "success")
        return redirect(url_for("student_dashboard"))

    return render_template("student_change_password.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/student/dashboard")
@login_required(role="student")
def student_dashboard():
    ensure_payments_schema()
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE id = %s", (session["user_id"],))
    student = cur.fetchone()
    student_cols = student_column_map()
    profile = student_profile_data(student, student_cols, fallback_name=session.get("name", "Student"))
    finance = {"fee_total": 0.0, "paid_amount": 0.0, "balance": 0.0}
    if student:
        finance = sync_student_fee(
            session["user_id"],
            profile.get("specialty", ""),
            profile.get("program_level", ""),
        )
    cur.execute(
        "SELECT * FROM payments WHERE student_id = %s ORDER BY created_at DESC",
        (session["user_id"],),
    )
    payments = cur.fetchall()
    unseen_paid = [
        p for p in payments
        if (p.get("status") or "").lower() == "paid" and int(p.get("student_seen") or 0) == 0
    ]
    if unseen_paid:
        set_banner(translate("payment_approved_notice"), "success")
        cur.execute(
            "UPDATE payments SET student_seen = 1 WHERE student_id = %s AND status = 'Paid' AND student_seen = 0",
            (session["user_id"],),
        )
        conn.commit()
    cur.close()
    conn.close()
    paid_payments = [p for p in payments if (p.get("status") or "").lower() == "paid"]
    return render_template(
        "student_dashboard.html",
        student=student,
        student_profile=profile,
        payments=payments,
        paid_payments=paid_payments,
        academic_year=current_academic_year(),
        fee_total=finance["fee_total"],
        paid_amount=finance["paid_amount"],
        fee_balance=finance["balance"],
    )


@app.route("/student/receipt/<transaction_id>")
@login_required(role="student")
def student_receipt(transaction_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    student_cols = student_column_map()
    name_expr = student_select_expr("full_name", student_cols["name"], "Student")
    matricule_expr = student_select_expr("matricule", student_cols["matricule"], "undefined")
    specialty_expr = student_select_expr("specialty", student_cols["specialty"], "")
    program_level_expr = student_select_expr("program_level", student_cols["program_level"], "")
    phone_expr = student_select_expr("student_phone", student_cols["phone"], "")
    dob_expr = student_select_expr("student_dob", student_cols["dob"], "")
    cur.execute(
        f"SELECT p.*, {name_expr}, {matricule_expr}, {specialty_expr}, {program_level_expr}, {phone_expr}, {dob_expr}, "
        "s.fee_total AS student_fee_total, s.paid_amount AS student_paid_amount, s.balance_amount AS student_balance_amount "
        "FROM payments p JOIN students s ON p.student_id = s.id "
        "WHERE p.transaction_id = %s AND p.student_id = %s",
        (transaction_id, session["user_id"]),
    )
    payment = cur.fetchone()
    payment_history = []
    if payment:
        cur.execute(
            "SELECT transaction_id, amount, status, created_at "
            "FROM payments WHERE student_id = %s ORDER BY created_at DESC",
            (session["user_id"],),
        )
        payment_history = cur.fetchall()
    cur.close()
    conn.close()

    if not payment:
        flash("Receipt not found for your account.", "error")
        return redirect(url_for("student_dashboard"))

    status_value = (payment.get("status") or "").strip().lower()
    if status_value != "paid":
        if status_value == "void":
            flash(translate("receipt_void_notice"), "error")
        else:
            flash(translate("receipt_pending_notice"), "warning")
        return redirect(url_for("student_dashboard"))

    paid_amount = float(payment.get("student_paid_amount") or 0)
    fee_breakdown = build_fee_breakdown(
        payment.get("specialty") or "",
        payment.get("program_level") or "",
        paid_amount,
    )
    receipt_url = url_for("public_receipt", transaction_id=payment.get("transaction_id"), _external=True)
    qr_payload = build_receipt_qr_payload(payment, receipt_url=receipt_url)
    qr_data_uri = generate_qr_data_uri(qr_payload)
    return render_template(
        "receipt.html",
        payment=payment,
        installment_breakdown=fee_breakdown,
        payment_history=payment_history,
        qr_data_uri=qr_data_uri,
        qr_payload=qr_payload,
    )


@app.route("/receipt/<transaction_id>")
def public_receipt(transaction_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    student_cols = student_column_map()
    name_expr = student_select_expr("full_name", student_cols["name"], "Student")
    matricule_expr = student_select_expr("matricule", student_cols["matricule"], "undefined")
    specialty_expr = student_select_expr("specialty", student_cols["specialty"], "")
    program_level_expr = student_select_expr("program_level", student_cols["program_level"], "")
    phone_expr = student_select_expr("student_phone", student_cols["phone"], "")
    dob_expr = student_select_expr("student_dob", student_cols["dob"], "")
    cur.execute(
        f"SELECT p.*, {name_expr}, {matricule_expr}, {specialty_expr}, {program_level_expr}, {phone_expr}, {dob_expr}, "
        "s.fee_total AS student_fee_total, s.paid_amount AS student_paid_amount, s.balance_amount AS student_balance_amount "
        "FROM payments p JOIN students s ON p.student_id = s.id "
        "WHERE p.transaction_id = %s",
        (transaction_id,),
    )
    payment = cur.fetchone()
    payment_history = []
    if payment:
        cur.execute(
            "SELECT transaction_id, amount, status, created_at "
            "FROM payments WHERE student_id = %s ORDER BY created_at DESC",
            (payment.get("student_id"),),
        )
        payment_history = cur.fetchall()
    cur.close()
    conn.close()

    if not payment:
        flash("Receipt not found.", "error")
        return redirect(url_for("login"))

    status_value = (payment.get("status") or "").strip().lower()
    if status_value != "paid":
        flash("Receipt is available after payment approval.", "warning")
        return redirect(url_for("login"))

    paid_amount = float(payment.get("student_paid_amount") or 0)
    fee_breakdown = build_fee_breakdown(
        payment.get("specialty") or "",
        payment.get("program_level") or "",
        paid_amount,
    )
    qr_payload = build_receipt_qr_payload(payment, receipt_url=url_for("public_receipt", transaction_id=transaction_id, _external=True))
    qr_data_uri = generate_qr_data_uri(qr_payload)
    return render_template(
        "receipt.html",
        payment=payment,
        installment_breakdown=fee_breakdown,
        payment_history=payment_history,
        qr_data_uri=qr_data_uri,
        qr_payload=qr_payload,
    )


@app.route("/student/payment-success/<transaction_id>")
@login_required(role="student")
def student_payment_success(transaction_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT transaction_id, amount, created_at, status, academic_year, installment_label, fee_total, balance_after "
        "FROM payments "
        "WHERE transaction_id = %s AND student_id = %s",
        (transaction_id, session["user_id"]),
    )
    payment = cur.fetchone()
    cur.close()
    conn.close()

    if not payment:
        flash("Payment confirmation not found.", "error")
        return redirect(url_for("student_dashboard"))

    return render_template("payment_success.html", payment=payment)


@app.route("/student/payment-status/<transaction_id>")
@login_required(role="student")
def student_payment_status(transaction_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT status FROM payments WHERE transaction_id = %s AND student_id = %s",
        (transaction_id, session["user_id"]),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({"status": "NotFound"}), 404
    return jsonify({"status": row.get("status") or "Pending"})


@app.route("/student/pay", methods=["GET", "POST"])
@login_required(role="student")
def student_pay():
    ensure_payments_schema()
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE id = %s", (session["user_id"],))
    student = cur.fetchone()
    student_cols = student_column_map()
    fallback_name = session.get("name", "Student")
    profile = student_profile_data(student, student_cols, fallback_name=fallback_name)
    details_unlocked = True
    entered_code = ""
    entered_amount = ""
    entered_phone = ""
    entered_method = ""

    academic_year = current_academic_year()
    finance = {"fee_total": 0.0, "paid_amount": 0.0, "balance": 0.0}
    if student:
        finance = sync_student_fee(
            session["user_id"],
            profile.get("specialty", ""),
            profile.get("program_level", ""),
        )
    fee_total = float(finance["fee_total"] or 0)
    paid_amount = float(finance["paid_amount"] or 0)
    balance = float(finance["balance"] or 0)

    def render_pay(**kwargs):
        payload = {
            "student": student,
            "student_profile": profile,
            "details_unlocked": details_unlocked,
            "entered_amount": entered_amount,
            "entered_phone": entered_phone,
            "entered_method": entered_method,
            "academic_year": academic_year,
            "fee_total": fee_total,
            "paid_amount": paid_amount,
            "fee_balance": balance,
        }
        payload.update(kwargs)
        return render_template("student_pay.html", **payload)

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        payment_method = (request.form.get("payment_method") or "").strip().lower()
        phone = request.form.get("payment_phone", "").strip()
        pin = request.form.get("payment_pin", "").strip()
        entered_amount = amount
        entered_phone = phone
        entered_method = payment_method
        purpose = f"School Fees ({academic_year})"
        installment_label = None
        if balance <= 0:
            flash("Your fees are fully paid for this academic year.", "success")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)
        if not amount:
            flash("Amount is required.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        try:
            amount_value = float(amount)
            if amount_value < MIN_PAYMENT_XAF:
                flash(f"Minimum payment is {MIN_PAYMENT_XAF:.0f} frs.", "error")
                cur.close()
                conn.close()
                return render_pay(details_unlocked=details_unlocked)
            if amount_value > balance:
                flash("The amount entered exceeds the remaining school fee balance.", "error")
                cur.close()
                conn.close()
                return render_pay(details_unlocked=details_unlocked)
        except ValueError:
            flash("Amount must be a valid number.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        if payment_method not in {"mtn", "orange"}:
            flash("Select a payment method.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        if not phone:
            flash("Phone number is required.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        if payment_method == "mtn" and not is_mtn_number(phone):
            transaction_id = f"TRX-{uuid.uuid4().hex[:10].upper()}"
            confirmation_code = str(random.randint(100000, 999999))
            try:
                cur.execute(
                    "INSERT INTO payments (student_id, transaction_id, amount, purpose, phone, status, confirmation_code, payment_method, "
                    "academic_year, installment_label, fee_total, balance_after) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        session["user_id"],
                        transaction_id,
                        amount_value,
                        purpose,
                        phone,
                        "Void",
                        confirmation_code,
                        "MTN MoMo",
                        academic_year,
                        installment_label,
                        fee_total,
                        max(balance - amount_value, 0),
                    ),
                )
                conn.commit()
            except MySQLError:
                pass
            flash("Phone number must be a valid MTN MoMo number.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        if payment_method == "orange" and not is_orange_number(phone):
            transaction_id = f"TRX-{uuid.uuid4().hex[:10].upper()}"
            confirmation_code = str(random.randint(100000, 999999))
            try:
                cur.execute(
                    "INSERT INTO payments (student_id, transaction_id, amount, purpose, phone, status, confirmation_code, payment_method, "
                    "academic_year, installment_label, fee_total, balance_after) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        session["user_id"],
                        transaction_id,
                        amount_value,
                        purpose,
                        phone,
                        "Void",
                        confirmation_code,
                        "Orange Money",
                        academic_year,
                        installment_label,
                        fee_total,
                        max(balance - amount_value, 0),
                    ),
                )
                conn.commit()
            except MySQLError:
                pass
            flash("Phone number must be a valid Orange Money number.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        if not re.fullmatch(r"\d{5}", pin):
            flash("PIN must be exactly 5 digits.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        if pin != PAYMENT_SIM_PIN:
            transaction_id = f"TRX-{uuid.uuid4().hex[:10].upper()}"
            confirmation_code = str(random.randint(100000, 999999))
            try:
                cur.execute(
                    "INSERT INTO payments (student_id, transaction_id, amount, purpose, phone, status, confirmation_code, payment_method, "
                    "academic_year, installment_label, fee_total, balance_after) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        session["user_id"],
                        transaction_id,
                        amount_value,
                        purpose,
                        phone,
                        "Void",
                        confirmation_code,
                        "Orange Money" if payment_method == "orange" else "MTN MoMo",
                        academic_year,
                        installment_label,
                        fee_total,
                        max(balance - amount_value, 0),
                    ),
                )
                conn.commit()
            except MySQLError:
                flash("Payment attempt could not be recorded. Please try again.", "error")
                cur.close()
                conn.close()
                return render_pay(details_unlocked=details_unlocked)

            flash("INVALID PIN, PLEASE ENTER A CORRECT PIN", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        transaction_id = f"TRX-{uuid.uuid4().hex[:10].upper()}"
        confirmation_code = str(random.randint(100000, 999999))

        try:
            cur.execute(
                "INSERT INTO payments (student_id, transaction_id, amount, purpose, phone, status, confirmation_code, payment_method, "
                "academic_year, installment_label, fee_total, balance_after) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    session["user_id"],
                    transaction_id,
                    amount_value,
                    purpose,
                    phone,
                    "Pending",
                    confirmation_code,
                    "Orange Money" if payment_method == "orange" else "MTN MoMo",
                    academic_year,
                    installment_label,
                    fee_total,
                    max(balance - amount_value, 0),
                ),
            )
            conn.commit()
        except MySQLError as exc:
            err = str(exc)
            if "fk_payments_student" in err or "students_legacy" in err:
                flash(
                    "Database foreign key is still linked to students_legacy. "
                    "Update payments FK to reference students(id).",
                    "error",
                )
            else:
                flash("Payment failed due to a database error.", "error")
            cur.close()
            conn.close()
            return render_pay(details_unlocked=details_unlocked)

        cur.close()
        conn.close()
        flash("Payment submitted.", "success")
        session["popup_message"] = (
            f"Payment of {amount_value:.2f} XAF submitted to {APP_SCHOOL_NAME}. "
            f"Transaction ID: {transaction_id}. Awaiting admin approval."
        )
        return redirect(url_for("student_payment_success", transaction_id=transaction_id))

    cur.close()
    conn.close()
    return render_pay()


def fetch_admin_dashboard_data() -> dict:
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT IFNULL(SUM(amount), 0) AS total_amount, COUNT(*) AS total_payments FROM payments")
    totals = cur.fetchone()

    total_collected = fetch_school_total_collected()

    today = date.today().isoformat()
    cur.execute(
        "SELECT COUNT(*) AS today_count, IFNULL(SUM(amount), 0) AS today_amount "
        "FROM payments WHERE DATE(created_at) = %s AND status = 'Paid'",
        (today,),
    )
    todays = cur.fetchone()

    cur.execute(
        "SELECT transaction_id, amount, purpose, status, created_at "
        "FROM payments ORDER BY created_at DESC LIMIT 12"
    )
    recent_rows = cur.fetchall()

    cur.execute(
        "SELECT status, COUNT(*) AS count FROM payments GROUP BY status"
    )
    status_rows = cur.fetchall()
    status_counts = {"Paid": 0, "Pending": 0, "Void": 0}
    for row in status_rows:
        status_name = (row.get("status") or "").strip()
        if status_name in status_counts:
            status_counts[status_name] = int(row.get("count") or 0)

    week_start = date.today() - timedelta(days=6)
    week_end = date.today()
    cur.execute(
        "SELECT DATE(created_at) AS d, "
        "IFNULL(SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END), 0) AS paid_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Void' THEN amount ELSE 0 END), 0) AS void_amount "
        "FROM payments "
        "WHERE DATE(created_at) BETWEEN %s AND %s "
        "GROUP BY DATE(created_at) "
        "ORDER BY DATE(created_at)",
        (week_start.isoformat(), week_end.isoformat()),
    )
    weekly_rows = cur.fetchall()
    weekly_map = {}
    for row in weekly_rows:
        day_key = row["d"].isoformat() if hasattr(row["d"], "isoformat") else str(row["d"])
        weekly_map[day_key] = {
            "paid": float(row.get("paid_amount") or 0),
            "pending": float(row.get("pending_amount") or 0),
            "void": float(row.get("void_amount") or 0),
        }
    weekly_labels = []
    weekly_amounts = []
    weekly_paid_amounts = []
    weekly_pending_amounts = []
    weekly_void_amounts = []
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        weekly_labels.append(day.strftime("%a %d"))
        day_data = weekly_map.get(day.isoformat(), {"paid": 0.0, "pending": 0.0, "void": 0.0})
        paid_val = float(day_data.get("paid") or 0)
        pending_val = float(day_data.get("pending") or 0)
        void_val = float(day_data.get("void") or 0)
        weekly_paid_amounts.append(paid_val)
        weekly_pending_amounts.append(pending_val)
        weekly_void_amounts.append(void_val)
        weekly_amounts.append(paid_val + pending_val + void_val)

    ensure_students_fee_columns()
    cur.execute(
        "SELECT id, full_name, specialty, program_level, matricule, "
        "IFNULL(fee_total, 0) AS fee_total, IFNULL(paid_amount, 0) AS paid_amount, "
        "IFNULL(balance_amount, 0) AS balance_amount "
        "FROM students ORDER BY created_at DESC"
    )
    student_rows = cur.fetchall() or []

    cur.close()
    conn.close()

    recent = []
    for row in recent_rows:
        created_at = row.get("created_at")
        recent.append(
            {
                "transaction_id": row.get("transaction_id"),
                "amount": float(row.get("amount") or 0),
                "purpose": row.get("purpose") or "",
                "status": row.get("status") or "",
                "created_at_label": created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, "strftime") else "",
            }
        )

    fully_paid_students = [
        s for s in student_rows
        if float(s.get("fee_total") or 0) > 0 and float(s.get("paid_amount") or 0) >= float(s.get("fee_total") or 0)
    ]
    partial_students = [
        s for s in student_rows
        if float(s.get("paid_amount") or 0) > 0 and float(s.get("balance_amount") or 0) > 0
    ]
    unpaid_students = [s for s in student_rows if float(s.get("paid_amount") or 0) <= 0]

    return {
        "totals": {
            "total_amount": float((totals or {}).get("total_amount") or 0),
            "total_payments": int((totals or {}).get("total_payments") or 0),
            "total_collected": total_collected,
            "total_students": len(student_rows),
            "students_paid": len(fully_paid_students),
            "students_unpaid": len(unpaid_students),
            "students_partial": len(partial_students),
        },
        "todays": {
            "today_count": int((todays or {}).get("today_count") or 0),
            "today_amount": float((todays or {}).get("today_amount") or 0),
        },
        "recent": recent,
        "status_counts": status_counts,
        "weekly_labels": weekly_labels,
        "weekly_amounts": weekly_amounts,
        "weekly_paid_amounts": weekly_paid_amounts,
        "weekly_pending_amounts": weekly_pending_amounts,
        "weekly_void_amounts": weekly_void_amounts,
        "paid_students": fully_paid_students,
        "unpaid_students": unpaid_students,
        "partial_students": partial_students,
    }


@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    payload = fetch_admin_dashboard_data()
    return render_template(
        "admin_dashboard.html",
        totals=payload["totals"],
        todays=payload["todays"],
        recent=payload["recent"],
        status_counts=payload["status_counts"],
        weekly_labels=payload["weekly_labels"],
        weekly_amounts=payload["weekly_amounts"],
        weekly_paid_amounts=payload["weekly_paid_amounts"],
        weekly_pending_amounts=payload["weekly_pending_amounts"],
        weekly_void_amounts=payload["weekly_void_amounts"],
        paid_students=payload["paid_students"],
        unpaid_students=payload["unpaid_students"],
        partial_students=payload["partial_students"],
    )


@app.route("/admin/dashboard/live")
@login_required(role="admin")
def admin_dashboard_live():
    response = jsonify(fetch_admin_dashboard_data())
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/admin/contact-messages")
@login_required(role="admin")
def admin_contact_messages():
    ensure_contact_messages_schema()
    status = (request.args.get("status") or "").strip()
    q = (request.args.get("q") or "").strip()

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("UPDATE contact_messages SET admin_seen = 1 WHERE admin_seen = 0")
    conn.commit()
    query = "SELECT * FROM contact_messages WHERE 1=1"
    params = []

    if status in {"Open", "Flagged", "Replied"}:
        query += " AND status = %s"
        params.append(status)

    if q:
        query += " AND (full_name LIKE %s OR email LIKE %s OR subject LIKE %s)"
        q_like = f"%{q}%"
        params.extend([q_like, q_like, q_like])

    query += " ORDER BY CASE WHEN status = 'Open' THEN 0 ELSE 1 END, created_at DESC"
    cur.execute(query, params)
    messages = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin_contact_messages.html", messages=messages, status=status, q=q)


@app.route("/admin/contact-messages/<int:message_id>", methods=["GET", "POST"])
@login_required(role="admin")
def admin_contact_message_detail(message_id):
    ensure_contact_messages_schema()
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        action = (request.form.get("action") or "reply").strip()
        if action == "reopen":
            cur.execute(
                "UPDATE contact_messages "
                "SET status = 'Open', admin_reply = NULL, replied_by = NULL, replied_at = NULL, admin_seen = 1 "
                "WHERE id = %s",
                (message_id,),
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("Message reopened.", "warning")
            return redirect(url_for("admin_contact_message_detail", message_id=message_id))

        if action == "approve":
            cur.execute(
                "UPDATE contact_messages SET status = 'Open', admin_seen = 1 WHERE id = %s",
                (message_id,),
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("Message approved and marked Open.", "success")
            return redirect(url_for("admin_contact_message_detail", message_id=message_id))

        admin_reply = (request.form.get("admin_reply") or "").strip()
        if not admin_reply:
            cur.close()
            conn.close()
            flash("Reply cannot be empty.", "error")
            return redirect(url_for("admin_contact_message_detail", message_id=message_id))
        if contains_html_or_script(admin_reply):
            cur.close()
            conn.close()
            flash("HTML or script content is not allowed in replies.", "error")
            return redirect(url_for("admin_contact_message_detail", message_id=message_id))

        cur.execute(
            "UPDATE contact_messages "
            "SET admin_reply = %s, replied_by = %s, replied_at = NOW(), status = 'Replied', admin_seen = 1 "
            "WHERE id = %s",
            (admin_reply, session.get("name", "Admin"), message_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Feedback saved.", "success")
        return redirect(url_for("admin_contact_message_detail", message_id=message_id))

    cur.execute("UPDATE contact_messages SET admin_seen = 1 WHERE id = %s", (message_id,))
    conn.commit()
    cur.execute("SELECT * FROM contact_messages WHERE id = %s", (message_id,))
    message = cur.fetchone()
    cur.close()
    conn.close()

    if not message:
        flash("Message not found.", "error")
        return redirect(url_for("admin_contact_messages"))

    return render_template("admin_contact_message_detail.html", message=message)


def parse_report_dates() -> tuple[date, date]:
    today = date.today()
    default_from = today - timedelta(days=29)
    date_from_raw = (request.args.get("date_from") or "").strip()
    date_to_raw = (request.args.get("date_to") or "").strip()

    try:
        date_from = datetime.strptime(date_from_raw, "%Y-%m-%d").date() if date_from_raw else default_from
    except ValueError:
        flash("Invalid start date. Using last 30 days.", "warning")
        date_from = default_from

    try:
        date_to = datetime.strptime(date_to_raw, "%Y-%m-%d").date() if date_to_raw else today
    except ValueError:
        flash("Invalid end date. Using today.", "warning")
        date_to = today

    if date_from > date_to:
        date_from, date_to = date_to, date_from
        flash("Start and end dates were swapped because start was later than end.", "warning")

    return date_from, date_to


def build_report_payload(date_from: date, date_to: date) -> dict:
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT "
        "COUNT(*) AS total_payments, "
        "IFNULL(SUM(amount), 0) AS total_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END), 0) AS paid_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Void' THEN amount ELSE 0 END), 0) AS void_amount "
        "FROM payments "
        "WHERE DATE(created_at) BETWEEN %s AND %s",
        (date_from.isoformat(), date_to.isoformat()),
    )
    summary = cur.fetchone() or {}

    cur.execute(
        "SELECT "
        "DATE(created_at) AS day, "
        "COUNT(*) AS tx_count, "
        "IFNULL(SUM(amount), 0) AS total_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END), 0) AS paid_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END), 0) AS pending_amount, "
        "IFNULL(SUM(CASE WHEN status = 'Void' THEN amount ELSE 0 END), 0) AS void_amount "
        "FROM payments "
        "WHERE DATE(created_at) BETWEEN %s AND %s "
        "GROUP BY DATE(created_at) "
        "ORDER BY DATE(created_at) DESC",
        (date_from.isoformat(), date_to.isoformat()),
    )
    daily_rows = cur.fetchall() or []

    cur.close()
    conn.close()

    summary_out = {
        "total_payments": int(summary.get("total_payments") or 0),
        "total_amount": float(summary.get("total_amount") or 0),
        "paid_amount": float(summary.get("paid_amount") or 0),
        "pending_amount": float(summary.get("pending_amount") or 0),
        "void_amount": float(summary.get("void_amount") or 0),
    }

    daily_out = []
    for row in daily_rows:
        day = row.get("day")
        day_iso = day.isoformat() if hasattr(day, "isoformat") else str(day)
        daily_out.append(
            {
                "day": day_iso,
                "tx_count": int(row.get("tx_count") or 0),
                "total_amount": float(row.get("total_amount") or 0),
                "paid_amount": float(row.get("paid_amount") or 0),
                "pending_amount": float(row.get("pending_amount") or 0),
                "void_amount": float(row.get("void_amount") or 0),
            }
        )

    return {"summary": summary_out, "daily": daily_out}


@app.route("/admin/reports")
@login_required(role="admin")
def admin_reports():
    date_from, date_to = parse_report_dates()
    payload = build_report_payload(date_from, date_to)
    return render_template(
        "admin_reports.html",
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
        summary=payload["summary"],
        daily_rows=payload["daily"],
    )


@app.route("/admin/reports/export.csv")
@login_required(role="admin")
def admin_reports_export_csv():
    date_from, date_to = parse_report_dates()
    payload = build_report_payload(date_from, date_to)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["School Fee Report"])
    writer.writerow(["Date From", date_from.isoformat()])
    writer.writerow(["Date To", date_to.isoformat()])
    writer.writerow([])
    writer.writerow(["Summary"])
    writer.writerow(["Total Payments", payload["summary"]["total_payments"]])
    writer.writerow(["Total Amount", f'{payload["summary"]["total_amount"]:.2f}'])
    writer.writerow(["Paid Amount", f'{payload["summary"]["paid_amount"]:.2f}'])
    writer.writerow(["Pending Amount", f'{payload["summary"]["pending_amount"]:.2f}'])
    writer.writerow(["Void Amount", f'{payload["summary"]["void_amount"]:.2f}'])
    writer.writerow([])
    writer.writerow(["Daily Breakdown"])
    writer.writerow(["Date", "Transactions", "Total Amount", "Paid Amount", "Pending Amount", "Void Amount"])
    for row in payload["daily"]:
        writer.writerow(
            [
                row["day"],
                row["tx_count"],
                f'{row["total_amount"]:.2f}',
                f'{row["paid_amount"]:.2f}',
                f'{row["pending_amount"]:.2f}',
                f'{row["void_amount"]:.2f}',
            ]
        )

    filename = f"school_fee_report_{date_from.isoformat()}_to_{date_to.isoformat()}.csv"
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@app.route("/admin/payments")
@login_required(role="admin")
def admin_payments():
    q = request.args.get("q", "").strip()
    departments = get_departments()
    status = request.args.get("status", "").strip()

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    student_cols = student_column_map()
    name_expr = student_select_expr("full_name", student_cols["name"], "Student")
    matricule_expr = student_select_expr("matricule", student_cols["matricule"], "undefined")
    query = (
        f"SELECT p.*, {name_expr}, {matricule_expr} "
        "FROM payments p JOIN students s ON p.student_id = s.id WHERE 1=1"
    )
    params = []
    if q:
        q_filters = ["p.transaction_id LIKE %s"]
        if student_cols["name"]:
            q_filters.append(f"s.{student_cols['name']} LIKE %s")
        if student_cols["matricule"]:
            q_filters.append(f"s.{student_cols['matricule']} LIKE %s")
        query += " AND (" + " OR ".join(q_filters) + ")"
        q_like = f"%{q}%"
        params += [q_like] * len(q_filters)
    if status:
        query += " AND p.status = %s"
        params.append(status)

    specialty = (request.args.get("specialty") or "").strip()
    if specialty and student_cols["specialty"]:
        query += f" AND s.{student_cols['specialty']} = %s"
        params.append(specialty)

    query += " ORDER BY p.created_at DESC"

    cur.execute(query, params)
    payments = cur.fetchall()

    enriched = []
    for payment in payments:
        student_id = payment.get("student_id")
        if not student_id:
            enriched.append(payment)
            continue
        cur.execute(
            "SELECT specialty, program_level, IFNULL(fee_total, 0) AS fee_total, "
            "IFNULL(paid_amount, 0) AS paid_amount, IFNULL(balance_amount, 0) AS balance_amount "
            "FROM students WHERE id = %s",
            (student_id,),
        )
        student = cur.fetchone() or {}
        fee_total = float(student.get("fee_total") or 0)
        paid_amount = float(student.get("paid_amount") or 0)
        plan = get_installment_plan(
            student.get("specialty", ""),
            student.get("program_level", ""),
            fee_total,
        )
        running = 0.0
        inst_status = []
        for item in plan:
            running += float(item["amount"])
            inst_status.append("✓" if paid_amount >= running else "—")
        payment["specialty"] = student.get("specialty")
        payment["program_level"] = student.get("program_level")
        payment["installment_status"] = inst_status
        enriched.append(payment)

    payments = enriched

    cur.close()
    conn.close()

    return render_template(
        "admin_payments.html",
        payments=payments,
        q=q,
        status=status,
        departments=departments,
    )


@app.route("/admin/payments/<transaction_id>")
@login_required(role="admin")
def admin_payment_detail(transaction_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    student_cols = student_column_map()
    name_expr = student_select_expr("full_name", student_cols["name"], "Student")
    matricule_expr = student_select_expr("matricule", student_cols["matricule"], "undefined")
    specialty_expr = student_select_expr("specialty", student_cols["specialty"], "")
    program_level_expr = student_select_expr("program_level", student_cols["program_level"], "")
    phone_expr = student_select_expr("phone", student_cols["phone"], "")
    dob_expr = student_select_expr("dob", student_cols["dob"], "")
    cur.execute(
        f"SELECT p.*, {name_expr}, {matricule_expr}, {specialty_expr}, {program_level_expr}, {phone_expr}, {dob_expr}, "
        "s.fee_total AS student_fee_total, s.paid_amount AS student_paid_amount, s.balance_amount AS student_balance_amount "
        "FROM payments p JOIN students s ON p.student_id = s.id WHERE p.transaction_id = %s",
        (transaction_id,),
    )
    payment = cur.fetchone()
    cur.close()
    conn.close()

    if not payment:
        flash("Payment not found.", "error")
        return redirect(url_for("admin_payments"))

    paid_amount = float(payment.get("student_paid_amount") or 0)
    fee_breakdown = build_fee_breakdown(
        payment.get("specialty") or "",
        payment.get("program_level") or "",
        paid_amount,
    )
    return render_template("admin_payment_detail.html", payment=payment, installment_breakdown=fee_breakdown)


@app.route("/admin/payments/<transaction_id>/confirm", methods=["POST"])
@login_required(role="admin")
def admin_confirm_payment(transaction_id):
    ensure_payments_schema()
    ensure_students_fee_columns()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE payments SET status = %s, approved_at = NOW(), approved_by = %s "
        "WHERE transaction_id = %s AND status = %s",
        ("Paid", session.get("name", "Admin"), transaction_id, "Pending"),
    )
    conn.commit()
    updated = cur.rowcount
    payment_row = None
    if updated:
        cur.execute("SELECT student_id, amount FROM payments WHERE transaction_id = %s", (transaction_id,))
        payment_row = cur.fetchone()
    cur.close()
    conn.close()
    if updated:
        log_admin_action("confirm", "payment", transaction_id, "Status set to Paid")
        if payment_row:
            student_id, amount = payment_row
            increment_school_total(float(amount or 0))
            try:
                conn2 = get_db()
                cur2 = conn2.cursor(dictionary=True)
                cur2.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                student = cur2.fetchone()
                cur2.close()
                conn2.close()
                if student:
                    student_cols = student_column_map()
                    profile = student_profile_data(student, student_cols)
                    sync_student_fee(
                        student_id,
                        profile.get("specialty", ""),
                        profile.get("program_level", ""),
                    )
            except MySQLError:
                pass
        flash("Payment confirmed.", "success")
    else:
        flash("Payment could not be confirmed (not in Pending state).", "warning")
    return redirect(url_for("admin_payment_detail", transaction_id=transaction_id))


@app.route("/admin/payments/<transaction_id>/void", methods=["POST"])
@login_required(role="admin")
def admin_void_payment(transaction_id):
    ensure_payments_schema()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE payments SET status = %s, approved_at = NOW(), approved_by = %s "
        "WHERE transaction_id = %s AND status IN (%s, %s)",
        (
            "Void",
            session.get("name", "Admin"),
            transaction_id,
            "Pending",
            "Paid",
        ),
    )
    conn.commit()
    updated = cur.rowcount
    cur.close()
    conn.close()
    if updated:
        log_admin_action("void", "payment", transaction_id, "Status set to Void")
        flash("Payment marked as Void.", "warning")
    else:
        flash("Payment could not be voided.", "error")
    return redirect(url_for("admin_payment_detail", transaction_id=transaction_id))


@app.route("/admin/payments/<transaction_id>/delete", methods=["POST"])
@login_required(role="admin")
def admin_delete_payment(transaction_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    cur.close()
    conn.close()
    log_admin_action("delete", "payment", transaction_id, "Payment record deleted")
    flash("Payment deleted permanently.", "warning")
    return redirect(url_for("admin_payments"))


@app.route("/admin/clear-payments", methods=["POST"])
@login_required(role="admin")
def admin_clear_payments():
    ensure_students_fee_columns()
    ensure_school_finance_schema()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments")
    cur.execute(
        "UPDATE students SET paid_amount = 0, balance_amount = IFNULL(fee_total, 0)"
    )
    cur.execute("UPDATE school_finance SET total_collected = 0 WHERE id = 1")
    conn.commit()
    cur.close()
    conn.close()
    flash("All payments cleared and balances reset.", "warning")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/departments", methods=["GET", "POST"])
@login_required(role="admin")
def admin_departments():
    ensure_departments_schema()
    edit_id = (request.args.get("edit_id") or "").strip()
    edit_department = None
    view_id = (request.args.get("view_id") or "").strip()
    view_department = None
    view_students = []
    if request.method == "POST":
        action = (request.form.get("action") or "add").strip()
        if action == "add":
            name = (request.form.get("name") or "").strip()
            code = (request.form.get("code") or "").strip()
            if not name:
                flash("Department name is required.", "error")
            else:
                try:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO departments (name, code) VALUES (%s, %s)",
                        (name, code),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    flash("Department added.", "success")
                except MySQLError:
                    flash("Department already exists or could not be saved.", "error")
        elif action == "update":
            dept_id = request.form.get("department_id")
            name = (request.form.get("name") or "").strip()
            code = (request.form.get("code") or "").strip()
            if dept_id and name:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE departments SET name = %s, code = %s WHERE id = %s",
                    (name, code, dept_id),
                )
                conn.commit()
                cur.close()
                conn.close()
                flash("Department updated.", "success")
        elif action == "delete":
            dept_id = request.form.get("department_id")
            if dept_id:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("DELETE FROM departments WHERE id = %s", (dept_id,))
                conn.commit()
                cur.close()
                conn.close()
                flash("Department deleted.", "warning")

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT d.*, "
        "(SELECT COUNT(*) FROM students s WHERE s.specialty = d.name) AS student_count "
        "FROM departments d ORDER BY d.name"
    )
    departments = cur.fetchall()
    if edit_id:
        cur.execute("SELECT * FROM departments WHERE id = %s", (edit_id,))
        edit_department = cur.fetchone()
    if view_id:
        cur.execute("SELECT * FROM departments WHERE id = %s", (view_id,))
        view_department = cur.fetchone()
        if view_department:
            student_cols = student_column_map()
            name_col = student_cols.get("name") or "full_name"
            mat_col = student_cols.get("matricule") or "matricule"
            level_col = student_cols.get("program_level") or "program_level"
            cur.execute(
                f"SELECT {name_col} AS full_name, {mat_col} AS matricule, {level_col} AS program_level "
                "FROM students WHERE specialty = %s ORDER BY created_at DESC",
                (view_department.get("name"),),
            )
            view_students = cur.fetchall() or []
    cur.close()
    conn.close()
    return render_template(
        "admin_departments.html",
        departments=departments,
        edit_department=edit_department,
        view_department=view_department,
        view_students=view_students,
    )


@app.route("/admin/fees", methods=["GET", "POST"])
@login_required(role="admin")
def admin_fees():
    ensure_fee_items_schema()
    ensure_departments_schema()
    edit_id = (request.args.get("edit_id") or "").strip()
    edit_fee = None
    view_id = (request.args.get("view_id") or "").strip()
    view_fee = None
    filter_department_id = (request.args.get("department_id") or "").strip()
    if request.method == "POST":
        action = (request.form.get("action") or "add").strip()
        department_id = request.form.get("department_id")
        program_level = (request.form.get("program_level") or "").strip()
        yearly_fee = (request.form.get("yearly_fee") or "").strip()
        fee_type = (request.form.get("fee_type") or "").strip()
        installment1 = (request.form.get("installment1") or "").strip()
        installment2 = (request.form.get("installment2") or "").strip()
        installment3 = (request.form.get("installment3") or "").strip()

        if action == "add":
            if not department_id or not program_level or not yearly_fee or not fee_type:
                flash("Department, level, fee type, and total fee are required.", "error")
            else:
                try:
                    fee_value = float(yearly_fee)
                    inst_values = []
                    if installment1 or installment2 or installment3:
                        if not (installment1 and installment2 and installment3):
                            flash("All three installments are required when you provide installments.", "error")
                            raise ValueError("Incomplete installments")
                        inst_values = [float(installment1), float(installment2), float(installment3)]
                        if abs(sum(inst_values) - fee_value) > 0.01:
                            flash("Installments must sum to the yearly fee.", "error")
                            raise ValueError("Installment sum mismatch")
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO fee_items (department_id, program_level, fee_type, total_fee, installment1, installment2, installment3) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (
                            department_id,
                            program_level,
                            fee_type,
                            fee_value,
                            inst_values[0] if inst_values else None,
                            inst_values[1] if inst_values else None,
                            inst_values[2] if inst_values else None,
                        ),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    flash("Fee structure saved.", "success")
                except (ValueError, MySQLError):
                    flash("Yearly fee must be a valid number.", "error")
        elif action == "update":
            fee_id = request.form.get("fee_id")
            if not fee_id or not department_id or not program_level or not yearly_fee or not fee_type:
                flash("Department, level, fee type, and total fee are required.", "error")
            else:
                try:
                    fee_value = float(yearly_fee)
                    inst_values = []
                    if installment1 or installment2 or installment3:
                        if not (installment1 and installment2 and installment3):
                            flash("All three installments are required when you provide installments.", "error")
                            raise ValueError("Incomplete installments")
                        inst_values = [float(installment1), float(installment2), float(installment3)]
                        if abs(sum(inst_values) - fee_value) > 0.01:
                            flash("Installments must sum to the yearly fee.", "error")
                            raise ValueError("Installment sum mismatch")
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE fee_items SET department_id = %s, program_level = %s, fee_type = %s, "
                        "total_fee = %s, installment1 = %s, installment2 = %s, installment3 = %s "
                        "WHERE id = %s",
                        (
                            department_id,
                            program_level,
                            fee_type,
                            fee_value,
                            inst_values[0] if inst_values else None,
                            inst_values[1] if inst_values else None,
                            inst_values[2] if inst_values else None,
                            fee_id,
                        ),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    flash("Fee structure updated.", "success")
                except (ValueError, MySQLError):
                    flash("Yearly fee must be a valid number.", "error")
        elif action == "delete":
            fee_id = request.form.get("fee_id")
            if fee_id:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("DELETE FROM fee_items WHERE id = %s", (fee_id,))
                conn.commit()
                cur.close()
                conn.close()
                flash("Fee structure deleted.", "warning")

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM departments ORDER BY name")
    departments = cur.fetchall()
    if edit_id:
        cur.execute(
            "SELECT id, department_id, program_level, fee_type, total_fee, installment1, installment2, installment3 "
            "FROM fee_items WHERE id = %s",
            (edit_id,),
        )
        edit_fee = cur.fetchone()
    if view_id:
        cur.execute(
            "SELECT fi.id, fi.department_id, d.name AS department_name, fi.program_level, fi.fee_type, "
            "fi.total_fee, fi.installment1, fi.installment2, fi.installment3 "
            "FROM fee_items fi JOIN departments d ON fi.department_id = d.id "
            "WHERE fi.id = %s",
            (view_id,),
        )
        view_fee = cur.fetchone()
    query = (
        "SELECT fi.id, d.name AS department_name, fi.program_level, fi.fee_type, fi.total_fee, "
        "fi.installment1, fi.installment2, fi.installment3 "
        "FROM fee_items fi JOIN departments d ON fi.department_id = d.id WHERE 1=1"
    )
    params = []
    if filter_department_id:
        query += " AND fi.department_id = %s"
        params.append(filter_department_id)
    query += " ORDER BY d.name, fi.program_level, fi.fee_type"
    cur.execute(query, params)
    fees = cur.fetchall()
    cur.close()
    conn.close()
    return render_template(
        "admin_fees.html",
        departments=departments,
        fees=fees,
        edit_fee=edit_fee,
        view_fee=view_fee,
    )


@app.route("/admin/students", methods=["GET", "POST"])
@login_required(role="admin")
def admin_students():
    q = request.args.get("q", "").strip()
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    student_cols = student_column_map()
    departments = get_departments()
    if request.method == "POST":
        action = (request.form.get("action") or "create").strip()
        if action == "create":
            full_name = request.form.get("full_name", "").strip()
            phone = request.form.get("phone", "").strip()
            specialty = request.form.get("specialty", "").strip()
            program_level = request.form.get("program_level", "").strip()
            matricule = request.form.get("matricule", "").strip()
            dob = request.form.get("dob", "").strip()
            email = request.form.get("email", "").strip()
            if not full_name or not matricule or not specialty or not program_level or not dob:
                flash("Full name, matricule, department, level, and date of birth are required.", "error")
            else:
                password = generate_temp_password()
                columns = []
                values = []
                for key, value in (
                    ("name", full_name),
                    ("phone", phone),
                    ("specialty", specialty),
                    ("program_level", program_level),
                    ("matricule", matricule),
                    ("dob", dob),
                    ("email", email),
                ):
                    col = student_cols.get(key)
                    if col:
                        columns.append(col)
                        values.append(value)
                password_col = student_cols.get("password") or "password_hash"
                columns.append(password_col)
                values.append(generate_password_hash(password))

                placeholders = ", ".join(["%s"] * len(columns))
                try:
                    cur.execute(
                        f"INSERT INTO students ({', '.join(columns)}) VALUES ({placeholders})",
                        tuple(values),
                    )
                    conn.commit()
                    if email:
                        sent, err = send_student_credentials_email(email, full_name, password)
                        if sent:
                            flash("Student created. Login details sent to email.", "success")
                        else:
                            flash(f"Student created. Email not sent: {err}", "warning")
                    else:
                        flash("Student created. No email provided to send login details.", "warning")
                except MySQLError:
                    flash("Student could not be created. Matricule or email might already exist.", "error")
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if q:
        q_filters = []
        if student_cols["matricule"]:
            q_filters.append(f"{student_cols['matricule']} LIKE %s")
        if student_cols["name"]:
            q_filters.append(f"{student_cols['name']} LIKE %s")
        if q_filters:
            query += " AND (" + " OR ".join(q_filters) + ")"
        q_like = f"%{q}%"
        params = [q_like] * len(q_filters)

    specialty = (request.args.get("specialty") or "").strip()
    if specialty and student_cols["specialty"]:
        query += f" AND {student_cols['specialty']} = %s"
        params.append(specialty)

    program_level = (request.args.get("program_level") or "").strip()
    if program_level and student_cols["program_level"]:
        query += f" AND {student_cols['program_level']} = %s"
        params.append(program_level)

    pay_status = (request.args.get("payment_status") or "").strip().lower()
    if pay_status == "paid":
        query += " AND IFNULL(paid_amount, 0) >= IFNULL(fee_total, 0) AND IFNULL(fee_total, 0) > 0"
    elif pay_status == "partial":
        query += " AND IFNULL(paid_amount, 0) > 0 AND IFNULL(balance_amount, 0) > 0"
    elif pay_status == "unpaid":
        query += " AND IFNULL(paid_amount, 0) = 0"

    query += " ORDER BY created_at DESC"
    cur.execute(query, params)
    students = cur.fetchall()

    total_paid = sum(float(s.get("paid_amount") or 0) for s in (students or []))
    cur.close()
    conn.close()
    return render_template(
        "admin_students.html",
        students=students,
        q=q,
        departments=departments,
        payment_status=pay_status,
        total_paid=total_paid,
    )


@app.route("/admin/students/<int:student_id>", methods=["GET", "POST"])
@login_required(role="admin")
def admin_student_detail(student_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    student_cols = student_column_map()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        specialty = request.form.get("specialty", "").strip()
        program_level = request.form.get("program_level", "").strip()
        matricule = request.form.get("matricule", "").strip()
        dob = request.form.get("dob", "").strip()

        update_fields = []
        update_values = []
        if student_cols["name"]:
            update_fields.append(f"{student_cols['name']} = %s")
            update_values.append(full_name)
        if student_cols["phone"]:
            update_fields.append(f"{student_cols['phone']} = %s")
            update_values.append(phone)
        if student_cols["specialty"]:
            update_fields.append(f"{student_cols['specialty']} = %s")
            update_values.append(specialty)
        if student_cols["program_level"]:
            update_fields.append(f"{student_cols['program_level']} = %s")
            update_values.append(program_level)
        if student_cols["matricule"]:
            update_fields.append(f"{student_cols['matricule']} = %s")
            update_values.append(matricule)
        if student_cols["dob"]:
            update_fields.append(f"{student_cols['dob']} = %s")
            update_values.append(dob)

        if update_fields:
            update_values.append(student_id)
            cur.execute(
                f"UPDATE students SET {', '.join(update_fields)} WHERE id = %s",
                tuple(update_values),
            )
            conn.commit()
            flash("Student updated.", "success")

    cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cur.fetchone()

    cur.execute(
        "SELECT * FROM payments WHERE student_id = %s ORDER BY created_at DESC",
        (student_id,),
    )
    payments = cur.fetchall()

    fee_total = float(student.get("fee_total") or 0)
    paid_amount = float(student.get("paid_amount") or 0)
    balance_amount = float(student.get("balance_amount") or 0)
    dept_value = student.get(student_cols.get("specialty") or "specialty", "")
    level_value = student.get(student_cols.get("program_level") or "program_level", "")
    fee_breakdown = build_fee_breakdown(dept_value, level_value, paid_amount)

    cur.close()
    conn.close()

    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("admin_students"))

    return render_template(
        "admin_student_detail.html",
        student=student,
        payments=payments,
        fee_total=fee_total,
        paid_amount=paid_amount,
        balance_amount=balance_amount,
        fee_breakdown=fee_breakdown,
    )


@app.route("/admin/students/<int:student_id>/delete", methods=["POST"])
@login_required(role="admin")
def admin_delete_student(student_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()

    if deleted:
        flash("Student deleted successfully.", "warning")
    else:
        flash("Student not found.", "error")
    return redirect(url_for("admin_students"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
