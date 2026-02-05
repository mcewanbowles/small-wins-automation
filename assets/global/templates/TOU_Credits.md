# Terms of Use & Credits Template

> **FILE:** `TOU_Credits.pdf`
> **INCLUDE IN:** Every product ZIP

---

## TERMS OF USE (Single-User Licence)

Thank you for purchasing from Small Wins Studio.

### YOU MAY
• Use with your own students/clients.
• Print, laminate, and store on your device and/or a secure school/clinic-approved drive.
• Use in a password-protected LMS/secure platform for your own students only.

### YOU MAY NOT
• Share publicly or with other staff/teams/parents/schools/clinics.
• Resell, redistribute, or claim as your own (in part or whole).
• Extract or redistribute PCS® symbols/images as standalone clipart or to make other products.

### LICENCE
One purchase = one teacher/therapist. Please buy extra licences for multiple staff.

{{#if BOOK_TITLE}}
### BOOK DISCLAIMER
This resource is designed to accompany "{{BOOK_TITLE}}". The book is not included and must be purchased/borrowed separately.
This product is not affiliated with, endorsed by, or sponsored by the author, publisher, or trademark holder.
{{/if}}

---

## CREDITS

© {{YEAR}} Small Wins Studio.

PCS® and Boardmaker® are trademarks of Tobii Dynavox LLC. Symbols used by the author under a licensed subscription.
Not affiliated with or endorsed by Tobii Dynavox.

---

## STORE

https://www.teacherspayteachers.com/store/small-wins-studio

---

## Implementation Notes

| Variable | Source | Example |
|----------|--------|---------|
| `{{YEAR}}` | `global_config.json → branding.copyright_year` | 2025 |
| `{{BOOK_TITLE}}` | `theme.json → book_adaptation.title` | "Brown Bear, Brown Bear" |

- If `BOOK_TITLE` is blank/missing, **omit the BOOK DISCLAIMER section entirely**.
