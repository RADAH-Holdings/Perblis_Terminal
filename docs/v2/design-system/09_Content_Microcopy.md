# 09 · Content & Microcopy

## 1. Voice
British English, plant-hire vocabulary (Lexicon 02 is binding: *hire, enquire, yard, on hire, off-hire, supplier, plant*). Register: **competent foreman** — direct, calm, specific, zero hype. Contractions fine ("you'll"), slang no, exclamation marks never, emoji never. Sentence case everywhere (stamps/overlines excepted).

**The three copy laws:**
1. Money copy is contractual — exact figures, who pays whom, when. Hirer surfaces: "You'll pay ₦900,000 now." Supplier surfaces: "You receive ₦810,000 after Terminal's service fee." **Never mix audiences: fee and payout figures appear on supplier/Ops surfaces only (D-014).**
2. Status copy states fact + next actor. "Awaiting supplier — they have 18 hours to respond."
3. Never blame the user; name the fix. ✗ "Invalid input" → ✓ "Enter an 11-digit phone number, e.g. 0803 123 4567."

## 2. Formats (normative)
| Thing | Format | Example |
|---|---|---|
| Money | ₦ + thin-space groups, no kobo | ₦1,250,000 |
| Money compact (pins/deltas only) | 1 decimal | ₦1.25M |
| Date | D MMM YYYY | 12 Jun 2026 |
| Date range | arrow + duration | 12 Jun → 26 Jun · 14 days |
| Time | 24h | 14:30 |
| Relative time | <1h "12 min ago"; <24h "14:30"; else date | — |
| Countdown | H:MM:SS mono | 3:42:10 |
| Distance | 1 decimal km | 4.3 km |
| Phone display | grouped | 0803 123 4567 |
| Units | value + space + unit | 22 t · 1.2 m³ · 450 TEU · 1,200 sqm |
| Hire ID | T- prefix + 4+ digits mono | T-2941 |
| Coordinates (ops) | 4 decimals | 6.4541, 3.3947 |

## 3. Status Vocabulary (single source)
| Status | Hirer sees | Supplier sees |
|---|---|---|
| requested | "Awaiting supplier" | "Action needed — respond in {h}h" |
| accepted | "Pay within {countdown}" | "Awaiting payment" |
| confirmed | "Confirmed — starts {date}" | "Confirmed — prepare for handover" |
| on_hire | "On hire" | "On hire" |
| completed | "Completed" | "Completed — payout queued" |
| declined | "Declined: {reason}" | "You declined" |
| expired | "Request expired — supplier didn't respond" | "Expired — you missed this request" |
| cancelled | "Cancelled by {party}" | same |
| in_dispute | "In dispute — payout frozen" | same |

## 4. Message Catalogs

### Auth & verification
OTP sent: "Code sent to 0803 123 4567" · OTP wrong: "That code didn't match. {n} attempts left." · Locked out: "Too many tries. Wait 15 minutes or reset your password." · Verification submitted: "Documents received. We review within 12 hours — you can browse meanwhile." · Rejected: "We couldn't verify: {reason}. Fix and resubmit."

### Hires & payments
Request sent: "Request sent. {Supplier} has 24 hours to respond." · Conflict 409: "Those dates were just taken. Here's what's still free." · Payment success: "Paid. Your hire is confirmed — receipt sent to {email}." · Payment failed: "{Paystack reason in plain words}. {n} attempts left, {countdown} remaining." · Window expired: "Payment window closed and the dates were released. You can request again." · Cancel w/ refund preview: "You'll be refunded {amount} ({rule applied}). This can't be undone."

### Listings
Publish blocked: "3 things before this goes live:" + checklist · Live: "Live. Your asset is now on the map." · Report received (reporter): "Thanks — our team reviews within 24 hours."

### Masking & policy
Masked notice: "Numbers unlock after payment — Terminal protects both parties." · Bypass warning (Ops-triggered): "Sharing contacts before payment breaches Terminal's terms. Repeated breaches suspend accounts."

### Empty/system
Offline: "Offline — showing saved data" · Map tiles down: "Map unavailable. Showing nearest assets as a list."

## 5. Buttons & Labels (canon)
Request to hire · Enquire · Accept hire · Decline hire · Pay now · Confirm handover · Mark off-hire · Cancel hire · Add asset · Publish · Pause listing · Duplicate · Save yard · Verify identity · Message supplier/hirer. Never: "Submit", "OK", "Yes/No" pairs (always verb pairs: "Cancel hire / Keep hire").

## 6. Legal & Trust Strings
Acknowledgments (checkbox, verbatim from Policy Bible §12.2) render in manifest-block style with scroll-required full text. Fee disclosure appears on supplier surfaces only, near payout totals: "Terminal's service fee: {fee_basis}." Hirer surfaces carry no fee copy (D-014); ToS discloses the platform-fee model in legal terms. NDPR footer on receipts/emails: "Terminal Ltd · Lagos · Data: terminal.africa/privacy". Support: every terminal email footer + error screen carries `support@` + WhatsApp business line (founder-operated in MVP).
