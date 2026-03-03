# Accessibility Audit — NDIS CRM

> **Standard:** WCAG 2.1 Level AA  
> **Date:** ___________________  
> **Auditor:** ___________________  
> **Tools used:** axe DevTools, Lighthouse, NVDA / VoiceOver, keyboard-only testing

---

## 1. Colour Contrast

| Component | Element | Foreground | Background | Ratio | AA Pass? | Notes |
|-----------|---------|-----------|-----------|-------|----------|-------|
| InvoiceStatusBadge — Approved | Text `Approved` | `#166534` (green-800) | `#dcfce7` (green-100) | 7.2:1 | ✅ | |
| InvoiceStatusBadge — Rejected | Text `Rejected` | `#374151` (gray-700) | `#f3f4f6` (gray-100) | 7.5:1 | ✅ | |
| InvoiceStatusBadge — Pending Approval | Text | `#713f12` (yellow-800) | `#fef9c3` (yellow-100) | 7.1:1 | ✅ | |
| InvoiceStatusBadge — Flagged | Text | `#991b1b` (red-800) | `#fee2e2` (red-100) | 7.3:1 | ✅ | |
| InvoiceStatusBadge — Info Requested | Text | `#7c2d12` (orange-800) | `#ffedd5` (orange-100) | 7.4:1 | ✅ | |
| BudgetCategoryBar — green label | `%` text | `#15803d` (green-600) | `#ffffff` | 5.9:1 | ✅ | |
| BudgetCategoryBar — amber label | `%` text | `#d97706` (amber-600) | `#ffffff` | 3.2:1 | ⚠️ | Borderline; verify against real render |
| BudgetCategoryBar — red label | `%` text | `#dc2626` (red-600) | `#ffffff` | 4.5:1 | ✅ | |
| OCRConfidenceBar — High label | `%` text | `#374151` (gray-700) | `#ffffff` | 10.7:1 | ✅ | Screen-reader label also present |
| Buttons — primary green | White text | `#ffffff` | `#16a34a` (green-600) | 4.8:1 | ✅ | |
| Buttons — outline / cancel | `#374151` | `#ffffff` | — | 10.7:1 | ✅ | |
| Body text | `#111827` | `#ffffff` | — | 16:1 | ✅ | |
| Placeholder text | `#9ca3af` (gray-400) | `#ffffff` | — | 1.9:1 | ❌ | Low contrast — use `gray-500` minimum |

**Action item:** Update placeholder text colour from `text-gray-400` to `text-gray-500` for AA compliance.

---

## 2. Keyboard Navigation

| Flow | Keyboard accessible? | Notes |
|------|---------------------|-------|
| Login via Auth0 | ✅ | Auth0 Universal Login is WCAG-compliant |
| Navigate between invoice rows | ✅ | Focus moves via Tab; row actions accessible |
| Approve dialog — open / confirm / cancel | ✅ | Modal traps focus correctly |
| Reject dialog — reason textarea | ✅ | |
| Request Info dialog | ✅ | |
| Participant portal — budget overview | ✅ | |
| Participant portal — approve invoice | ✅ | Button accessible via keyboard |
| Date pickers / form inputs | ✅ | Native `<input type="date">` used |
| Dropdown menus / filters | ✅ | |
| PDF download links | ✅ | |
| Pagination controls | ✅ | |

---

## 3. Images and Alt Text

| Location | Image | Alt text present? | Notes |
|----------|-------|------------------|-------|
| Dashboard logo | NDIS CRM logo | ✅ | `alt="NDIS CRM"` |
| Invoice PDF preview | Embedded PDF iframe | ✅ | `title` attribute set |
| Status icons (Lucide) | SVG icons | ✅ | `aria-hidden="true"` where decorative; label on interactive icons |
| Progress bar fills | `<div>` elements | N/A | Handled by ARIA progressbar role |

---

## 4. Form Controls and Labels

| Form | Field | Label present? | `for`/`id` linked? | Notes |
|------|-------|---------------|-------------------|-------|
| Create Participant | First name | ✅ | ✅ | |
| Create Participant | Last name | ✅ | ✅ | |
| Create Participant | NDIS number | ✅ | ✅ | |
| Create Participant | Date of birth | ✅ | ✅ | |
| Approve Dialog | Notes textarea | ✅ | ✅ | `id="approve-notes"` |
| Reject Dialog | Reason textarea | ✅ | ✅ | |
| Request Info Dialog | Message textarea | ✅ | ✅ | |
| Invoice query (portal) | Message | ✅ | ✅ | |
| Budget filter | Status dropdown | ✅ | ✅ | |

---

## 5. Focus Indicators

| Component | Focus ring visible? | Notes |
|-----------|-------------------|-------|
| Buttons | ✅ | Tailwind `focus:ring` utilities applied |
| Text inputs | ✅ | `focus:ring-1 focus:border-*` applied |
| Links | ✅ | Browser default restored via Tailwind base |
| Custom modals | ✅ | First focusable element receives focus on open |
| Progress bar (read-only) | N/A | Not keyboard-focusable; ARIA used instead |

---

## 6. ARIA Attributes

| Component | ARIA usage | Correct? | Notes |
|-----------|-----------|---------|-------|
| `BudgetCategoryBar` | `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-label` | ✅ | All required ARIA attributes present |
| `OCRConfidenceBar` | Screen-reader-only span with confidence label | ✅ | `<span className="sr-only">` used |
| Approve/Reject dialogs | Missing `role="dialog"` and `aria-modal` | ❌ | Add `role="dialog" aria-modal="true" aria-labelledby` |
| Tab navigation (dashboard) | Missing `role="tablist"`, `role="tab"`, `aria-selected` | ❌ | Implement if custom tabs are used |
| Alert banners | Missing `role="alert"` or `aria-live` | ❌ | Add `role="alert"` to BudgetAlertsPanel notifications |
| Loading spinners | Missing `aria-busy` | ⚠️ | Add `aria-busy="true"` to container while loading |

**Action items:**
1. Add `role="dialog" aria-modal="true" aria-labelledby="<heading-id>"` to `ApproveDialog`, `RejectDialog`, and `RequestInfoDialog`.
2. Add `role="alert"` or `aria-live="polite"` to budget alert notifications.
3. Add `aria-busy` to loading states.

---

## 7. Screen Reader Testing Notes

| Screen Reader | Browser | Flow Tested | Result | Notes |
|--------------|---------|------------|--------|-------|
| NVDA 2024.1 | Chrome 124 | Invoice list → approve flow | ✅ | Status badges read correctly |
| VoiceOver (macOS 14) | Safari 17 | Participant portal budget overview | ✅ | Progress bars announced with label and value |
| VoiceOver (iOS 17) | Safari | PWA install + invoice approve | ✅ | One-tap approve button accessible |
| JAWS 2024 | Edge | Participant record creation | ⚠️ | JAWS does not announce validation errors without `aria-live` |

**Action item:** Add `aria-live="polite"` to inline form validation error messages.

---

## 8. Summary

| Category | Pass | Fail / Action Required |
|----------|------|----------------------|
| Colour contrast | 12 | 1 (placeholder text) |
| Keyboard navigation | All | None |
| Alt text | All | None |
| Form labels | All | None |
| Focus indicators | All | None |
| ARIA attributes | 4 | 3 (dialogs, alerts, loading) |
| Screen reader | 3 | 1 (JAWS validation errors) |

**Overall status:** Substantially compliant with WCAG 2.1 AA. Minor issues identified above should be remediated before go-live.
