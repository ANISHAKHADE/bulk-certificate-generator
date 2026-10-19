from email_validator import validate_email, EmailNotValidError
from dataclasses import dataclass
from typing import List, Any
from app.certificates.fonts import unsupported_chars

@dataclass
class ValidatedRow:
    index: int
    name: str
    email: str
    errors: List[str]

def validate_recipients(raw_rows: List[Any]) -> List[ValidatedRow]:
    results = []
    seen_emails = set()
    for i, row in enumerate(raw_rows):
        errors = []
        name = getattr(row, "name", None)
        email = getattr(row, "email", None)
        
        if not isinstance(name, str):
            errors.append("name is required")
            name_clean = str(name) if name else ""
        else:
            name_clean = " ".join(name.split())
            if not name_clean: errors.append("name must not be blank")
            elif len(name_clean) > 100: errors.append("name must be at most 100 characters")
            else:
                bad_chars = unsupported_chars(name_clean)
                if bad_chars: errors.append(f"name contains unsupported characters: {''.join(bad_chars)}")

        email_clean = ""
        if not isinstance(email, str):
            errors.append("email is invalid")
        else:
            try:
                valid = validate_email(email, check_deliverability=False)
                email_clean = valid.normalized
                if email_clean.lower() in seen_emails: errors.append("duplicate email in this job")
                else: seen_emails.add(email_clean.lower())
            except EmailNotValidError:
                errors.append("email is invalid")
                email_clean = email

        results.append(ValidatedRow(i, name_clean, email_clean, errors))
    return results
