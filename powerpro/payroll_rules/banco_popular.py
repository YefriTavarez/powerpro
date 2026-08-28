"""Deterministic Banco Popular payroll fixed-width file generation.

The generator is intentionally independent from Frappe so the byte layout can
be tested without a site or database.  Callers must pass an approved snapshot;
this module never reads or changes payroll records.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


RECORD_WIDTH = 320
ENCODING = "cp1252"
POPULAR_ROUTING_CODE = "101010708"
DOP_CURRENCY_CODE = "214"
PAYROLL_SERVICE_CODE = "01"
CONTACT_METHOD_CODE = "1"
FILE_PREFIX = "PE"
FILE_SUFFIX = "E"
POPULAR_BANK_NAMES = {
    "BANCO POPULAR",
    "BANCO POPULAR DOMINICANO",
}

ACCOUNT_TYPES = {
    "ahorro": ("2", "32"),
    "corriente": ("1", "22"),
}

IDENTIFICATION_TYPES = {
    "cedula": "CE",
    "pasaporte": "PS",
    "rnc": "RN",
}


class BankFileValidationError(ValueError):
    """Raised when a value cannot be represented safely in the bank layout."""


@dataclass(frozen=True)
class BancoPopularProfile:
    activation_number: str
    company_identification: str
    registered_company_name: str
    service_code: str = PAYROLL_SERVICE_CODE
    routing_code: str = POPULAR_ROUTING_CODE
    currency: str = "DOP"
    contact_method: str = CONTACT_METHOD_CODE
    file_prefix: str = FILE_PREFIX
    file_suffix: str = FILE_SUFFIX


@dataclass(frozen=True)
class PayrollPayment:
    reference: str
    beneficiary_name: str
    bank_account_no: str
    account_type: str
    identification_type: str
    identification_number: str
    amount: Decimal | str | int | float
    bank_name: str = "BANCO POPULAR DOMINICANO"
    currency: str = "DOP"
    email: str = ""


@dataclass(frozen=True)
class GeneratedBankFile:
    filename: str
    content: bytes
    sha256: str
    payment_count: int
    total_amount: Decimal


def build_payroll_file(
    profile: BancoPopularProfile,
    *,
    payment_date: date,
    payment_sequence: str,
    description: str,
    payments: Iterable[PayrollPayment],
) -> GeneratedBankFile:
    """Build one header and one 320-byte detail line per payroll payment."""
    normalized_profile = validate_profile(profile)
    sequence, description = validate_batch_instruction(
        payment_date=payment_date,
        payment_sequence=payment_sequence,
        description=description,
    )
    payment_rows = list(payments)
    if not payment_rows:
        raise BankFileValidationError("At least one payroll payment is required.")

    normalized_payments = [validate_payment(row, normalized_profile) for row in payment_rows]
    references = [row.reference for row in normalized_payments]
    duplicates = sorted(
        reference for reference in set(references) if references.count(reference) > 1
    )
    if duplicates:
        raise BankFileValidationError(
            f"Duplicate payment references are not allowed: {', '.join(duplicates)}"
        )

    total_cents = sum(_amount_to_cents(row.amount) for row in normalized_payments)
    if len(str(len(normalized_payments))) > 11:
        raise BankFileValidationError("Payment count exceeds the 11-digit bank field.")
    if len(str(total_cents)) > 13:
        raise BankFileValidationError("Payroll total exceeds the 13-digit bank field.")
    header = _build_header(
        normalized_profile,
        payment_date=payment_date,
        payment_sequence=sequence,
        payment_count=len(normalized_payments),
        total_cents=total_cents,
    )
    details = [
        _build_detail(
            normalized_profile,
            payment_date=payment_date,
            payment_sequence=sequence,
            description=description,
            transaction_sequence=index,
            payment=payment,
        )
        for index, payment in enumerate(normalized_payments, start=1)
    ]
    lines = [header, *details]
    for index, line in enumerate(lines, start=1):
        width = len(line.encode(ENCODING))
        if width != RECORD_WIDTH:
            raise AssertionError(f"Record {index} is {width} bytes; expected {RECORD_WIDTH}.")

    content = b"\r\n".join(line.encode(ENCODING) for line in lines) + b"\r\n"
    filename = (
        f"{normalized_profile.file_prefix}{normalized_profile.activation_number}"
        f"{normalized_profile.service_code}{payment_date:%m%d}{sequence}"
        f"{normalized_profile.file_suffix}.txt"
    )
    return GeneratedBankFile(
        filename=filename,
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        payment_count=len(normalized_payments),
        total_amount=(Decimal(total_cents) / Decimal("100")).quantize(Decimal("0.01")),
    )


def validate_batch_instruction(
    *, payment_date: date, payment_sequence: str, description: str
) -> tuple[str, str]:
    if not isinstance(payment_date, date):
        raise BankFileValidationError("Payment Date is required.")
    sequence = _fixed_digits(payment_sequence, 7, "Payment Sequence")
    clean_description = _clean_text(description)
    if not clean_description:
        raise BankFileValidationError("Payment Description is required.")
    return sequence, _fit_text(clean_description, 44, "Payment Description")


def validate_profile(profile: BancoPopularProfile) -> BancoPopularProfile:
    activation_number = _digits(profile.activation_number, "Activation Number", maximum=10)
    company_identification = _digits(
        profile.company_identification, "Company Identification", maximum=15
    )
    registered_company_name = _clean_text(profile.registered_company_name)
    if not registered_company_name:
        raise BankFileValidationError("Registered Company Name is required.")
    registered_company_name = _fit_text(
        registered_company_name, 35, "Registered Company Name"
    ).rstrip()
    service_code = _fixed_digits(profile.service_code, 2, "Service Code")
    if service_code != PAYROLL_SERVICE_CODE:
        raise BankFileValidationError(
            f"Banco Popular payroll v1 requires Service Code {PAYROLL_SERVICE_CODE}."
        )
    routing_code = _fixed_digits(profile.routing_code, 9, "Routing Code")
    if routing_code != POPULAR_ROUTING_CODE:
        raise BankFileValidationError(
            f"Banco Popular payroll v1 requires Routing Code {POPULAR_ROUTING_CODE}."
        )
    currency = _clean_text(profile.currency).upper()
    if currency != "DOP":
        raise BankFileValidationError("Banco Popular payroll v1 supports DOP only.")
    contact_method = _fixed_digits(profile.contact_method, 1, "Contact Method")
    if contact_method != CONTACT_METHOD_CODE:
        raise BankFileValidationError(
            f"Banco Popular payroll v1 requires Contact Method {CONTACT_METHOD_CODE}."
        )
    file_prefix = _compact_text(profile.file_prefix, "File Prefix", maximum=5).upper()
    if file_prefix != FILE_PREFIX:
        raise BankFileValidationError(
            f"Banco Popular payroll v1 requires File Prefix {FILE_PREFIX}."
        )
    file_suffix = _compact_text(profile.file_suffix, "File Suffix", maximum=5).upper()
    if file_suffix != FILE_SUFFIX:
        raise BankFileValidationError(
            f"Banco Popular payroll v1 requires File Suffix {FILE_SUFFIX}."
        )
    return BancoPopularProfile(
        activation_number=activation_number,
        company_identification=company_identification,
        registered_company_name=registered_company_name,
        service_code=service_code,
        routing_code=routing_code,
        currency=currency,
        contact_method=contact_method,
        file_prefix=file_prefix,
        file_suffix=file_suffix,
    )


def validate_payment(
    payment: PayrollPayment, profile: BancoPopularProfile
) -> PayrollPayment:
    reference = _compact_text(payment.reference, "Payment Reference", maximum=140)
    beneficiary_name = _clean_text(payment.beneficiary_name)
    if not beneficiary_name:
        raise BankFileValidationError(f"{reference}: Beneficiary Name is required.")
    _ensure_encodable(beneficiary_name, f"{reference}: Beneficiary Name")

    bank_name = _clean_text(payment.bank_name).upper()
    if bank_name not in POPULAR_BANK_NAMES:
        raise BankFileValidationError(
            f"{reference}: only Banco Popular destination accounts are supported in v1."
        )
    bank_account_no = _digits(payment.bank_account_no, f"{reference}: Bank Account", maximum=20)
    account_type = _normalize_choice(payment.account_type, ACCOUNT_TYPES, "Account Type", reference)
    identification_type = _normalize_choice(
        payment.identification_type,
        IDENTIFICATION_TYPES,
        "Identification Type",
        reference,
    )
    if _choice_key(identification_type) == "pasaporte":
        identification_number = _compact_text(
            payment.identification_number,
            f"{reference}: Identification Number",
            maximum=15,
        ).upper()
    else:
        identification_number = _digits(
            payment.identification_number,
            f"{reference}: Identification Number",
            maximum=15,
        )
    currency = _clean_text(payment.currency).upper()
    if currency != profile.currency:
        raise BankFileValidationError(
            f"{reference}: payment currency {currency or '(blank)'} "
            f"does not match {profile.currency}."
        )
    email = _clean_text(payment.email)
    _fit_text(email, 133, f"{reference}: Email")
    _amount_to_cents(payment.amount)
    return PayrollPayment(
        reference=reference,
        beneficiary_name=beneficiary_name,
        bank_account_no=bank_account_no,
        account_type=account_type,
        identification_type=identification_type,
        identification_number=identification_number,
        amount=Decimal(str(payment.amount)),
        bank_name=bank_name,
        currency=currency,
        email=email,
    )


def _build_header(
    profile: BancoPopularProfile,
    *,
    payment_date: date,
    payment_sequence: str,
    payment_count: int,
    total_cents: int,
) -> str:
    effective_date = payment_date.strftime("%Y%m%d")
    return "".join(
        (
            "H",
            _fit_text(profile.company_identification, 15, "Company Identification"),
            _fit_text(profile.registered_company_name, 35, "Registered Company Name"),
            payment_sequence,
            profile.service_code,
            effective_date,
            "0" * 11,
            "0" * 13,
            str(payment_count).zfill(11),
            str(total_cents).zfill(13),
            "0" * 15,
            effective_date,
            "0" * 4,
            " " * 177,
        )
    )


def _build_detail(
    profile: BancoPopularProfile,
    *,
    payment_date: date,
    payment_sequence: str,
    description: str,
    transaction_sequence: int,
    payment: PayrollPayment,
) -> str:
    del payment_date  # Reserved for versioned layouts; v1 uses it only in the header and filename.
    account_type_code, operation_code = ACCOUNT_TYPES[_choice_key(payment.account_type)]
    identification_type_code = IDENTIFICATION_TYPES[_choice_key(payment.identification_type)]
    beneficiary = _clean_text(payment.beneficiary_name)[:35]
    return "".join(
        (
            "N",
            _fit_text(profile.company_identification, 15, "Company Identification"),
            payment_sequence,
            str(transaction_sequence).zfill(7),
            _fit_text(payment.bank_account_no, 20, "Bank Account"),
            account_type_code,
            DOP_CURRENCY_CODE,
            profile.routing_code,
            operation_code,
            str(_amount_to_cents(payment.amount)).zfill(13),
            identification_type_code,
            _fit_text(payment.identification_number, 15, "Identification Number"),
            _fit_text(beneficiary, 47, "Beneficiary Name"),
            _fit_text(description.rstrip(), 44, "Payment Description"),
            profile.contact_method,
            _fit_text(payment.email, 133, "Email"),
        )
    )


def _amount_to_cents(value: Decimal | str | int | float) -> int:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as exc:
        raise BankFileValidationError(f"Invalid payment amount: {value!r}.") from exc
    if amount <= 0:
        raise BankFileValidationError("Payment amount must be greater than zero.")
    cents = int(amount * 100)
    if len(str(cents)) > 13:
        raise BankFileValidationError("Payment amount exceeds the 13-digit bank field.")
    return cents


def _normalize_choice(value: str, choices: dict, label: str, reference: str) -> str:
    key = _choice_key(value)
    if key not in choices:
        allowed = ", ".join(choice.title() for choice in choices)
        raise BankFileValidationError(f"{reference}: {label} must be one of {allowed}.")
    return key.title()


def _choice_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", _clean_text(value))
    return "".join(character for character in text if not unicodedata.combining(character)).lower()


def _digits(value: str, label: str, *, maximum: int) -> str:
    raw = _clean_text(value)
    digits = re.sub(r"[\s-]", "", raw)
    if not digits or not digits.isdigit():
        raise BankFileValidationError(f"{label} must contain digits only.")
    if len(digits) > maximum:
        raise BankFileValidationError(f"{label} exceeds {maximum} digits.")
    return digits


def _fixed_digits(value: str, width: int, label: str) -> str:
    digits = _digits(value, label, maximum=width)
    if len(digits) != width:
        raise BankFileValidationError(f"{label} must contain exactly {width} digits.")
    return digits


def _compact_text(value: str, label: str, *, maximum: int) -> str:
    text = _clean_text(value)
    if not text or any(character.isspace() for character in text):
        raise BankFileValidationError(f"{label} is required and cannot contain spaces.")
    _ensure_encodable(text, label)
    if len(text.encode(ENCODING)) > maximum:
        raise BankFileValidationError(f"{label} exceeds {maximum} bytes.")
    return text


def _fit_text(value: str, width: int, label: str) -> str:
    text = _clean_text(value)
    _ensure_encodable(text, label)
    length = len(text.encode(ENCODING))
    if length > width:
        raise BankFileValidationError(f"{label} exceeds {width} bytes.")
    return text + (" " * (width - length))


def _clean_text(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or "").replace("\u00a0", " "))
    return re.sub(r"\s+", " ", text).strip()


def _ensure_encodable(value: str, label: str) -> None:
    try:
        value.encode(ENCODING)
    except UnicodeEncodeError as exc:
        raise BankFileValidationError(
            f"{label} contains a character that is not supported by {ENCODING}."
        ) from exc
