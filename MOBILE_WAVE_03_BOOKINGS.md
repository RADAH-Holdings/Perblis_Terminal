# TERMINAL MOBILE — WAVE 03: BOOKINGS
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 02 must be complete before starting this wave.

---

## Context

This wave implements the full booking lifecycle from both renter and owner perspectives. After this wave, renters can request bookings, owners can accept/decline, either party can cancel, and payment can be simulated.

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/bookings/` | List bookings (role filter) |
| `POST` | `/api/v1/bookings/` | Create a booking request |
| `GET` | `/api/v1/bookings/{id}/` | Booking detail |
| `PATCH` | `/api/v1/bookings/{id}/accept/` | Owner accepts |
| `PATCH` | `/api/v1/bookings/{id}/decline/` | Owner declines |
| `PATCH` | `/api/v1/bookings/{id}/cancel/` | Either party cancels |
| `PATCH` | `/api/v1/bookings/{id}/pay/` | Mark as paid (simulated) |

---

## Step 1: API functions

**File: `src/api/bookings.ts`**

```typescript
import { apiClient } from './client';

export const bookingsApi = {
  list: (params?: { role?: string; status?: string }) =>
    apiClient.get('/bookings/', { params }),

  getById: (id: string) =>
    apiClient.get(`/bookings/${id}/`),

  create: (data: {
    listing_id: string;
    start_date: string;
    end_date: string;
    duration_type: 'daily' | 'weekly' | 'monthly';
    renter_note?: string;
  }) => apiClient.post('/bookings/', data),

  accept: (id: string) =>
    apiClient.patch(`/bookings/${id}/accept/`),

  decline: (id: string, reason?: string) =>
    apiClient.patch(`/bookings/${id}/decline/`, { reason }),

  cancel: (id: string, reason?: string) =>
    apiClient.patch(`/bookings/${id}/cancel/`, { reason }),

  markPaid: (id: string) =>
    apiClient.patch(`/bookings/${id}/pay/`),
};
```

---

## Step 2: Screens

### Create Booking (Bottom Sheet from Listing Detail)

**Triggered from**: "Book Now" button on listing detail screen

**UI requirements:**
- Bottom sheet (slide up, 70% screen height)
- Date range picker: start date, end date (calendar UI)
- Duration type selector: Daily | Weekly | Monthly (segment control)
- Price calculator (real-time, computed client-side):
  - Shows: `{days/weeks/months} × ₦{unit_price} = ₦{gross_amount}`
  - Commission line: `Platform fee (10%): ₦{commission}`
  - Total: `₦{gross_amount}`
- Renter note (optional textarea)
- "Request Booking" button
- Validation:
  - Start date must be in the future
  - End date must be after start date
  - Listing must have price for selected duration type

**Flow:**
1. User selects dates and duration type
2. Client calculates estimated price (for display only — server does final calc)
3. Submit → `POST /api/v1/bookings/`
4. On success → navigate to booking detail
5. On error (date conflict, own listing) → show error message

### My Bookings Screen (`app/(tabs)/bookings.tsx`)

**UI requirements:**
- Segmented control at top: "As Renter" | "As Owner"
- Status filter tabs: All, Pending, Confirmed, Completed, Cancelled
- List of booking cards
- Each card shows:
  - Listing title
  - Date range
  - Gross amount
  - Status badge (color-coded)
  - Other party's name + avatar
- Pull to refresh
- Empty states per filter

**Status badge colors:**
- Pending: `#f59e0b` (amber)
- Confirmed: `#10b981` (green)
- Declined: `#ef4444` (red)
- Active: `#3b82f6` (blue)
- Completed: `#6b7280` (gray)
- Cancelled: `#9ca3af` (light gray)

**Flow:**
1. Default role based on user's `is_renter` / `is_owner`
2. Fetch `GET /api/v1/bookings/?role=renter` or `?role=owner`
3. Optionally filter by `?status=pending`
4. Tap card → navigate to booking detail

### Booking Detail Screen (`app/booking/[id].tsx`)

**UI requirements:**
- Header: listing title, status badge
- Party info section:
  - "Renter" card (avatar, name, phone — tap to call)
  - "Owner" card (avatar, name, phone — tap to call)
- Date section: start → end, duration days, duration type
- Financial section:
  - Gross amount
  - Commission (10%)
  - Owner payout
  - Payment status badge
- Renter note (if any)
- Cancellation reason (if cancelled/declined)
- **Action buttons** (contextual based on status and user role):

| Status | User Role | Actions |
|---|---|---|
| `pending` | Owner | "Accept" (green), "Decline" (red) |
| `pending` | Renter | "Cancel Booking" |
| `confirmed` | Either | "Mark as Paid", "Cancel Booking" |
| `confirmed` | Either | "Message" (go to thread) |
| `declined/cancelled/completed` | Either | No actions (read-only) |

- "Go to Chat" button (if `thread_id` exists)

**Action flows:**
- Accept: Confirm dialog → `PATCH .../accept/` → refresh → show success
- Decline: Prompt for reason → `PATCH .../decline/` → refresh
- Cancel: Confirm + optional reason → `PATCH .../cancel/` → refresh
- Mark Paid: Confirm dialog → `PATCH .../pay/` → refresh → show success
- Message: Navigate to `thread/[thread_id]`

---

## Step 3: Booking status component

**File: `src/components/bookings/BookingStatusBadge.tsx`**

Props: `status: BookingStatus`

Returns a colored badge/pill with the status text. Use the color mapping above.

---

## Step 4: Date picker

Use a calendar date picker component (e.g., `react-native-calendars` or build custom). The picker should:
- Highlight the selected range
- Disable dates in the past
- Show the computed number of days/weeks/months below

---

## Step 5: Push notifications (prep only)

Prepare the notification structure (no actual push integration in MVP):
- When a booking status changes → the other party should eventually be notified
- Add a local notification utility stub that can be wired up later

---

## Definition of Done

- [ ] "Book Now" from listing detail opens booking creation bottom sheet
- [ ] Date picker with range selection (start/end)
- [ ] Duration type selector (daily/weekly/monthly)
- [ ] Real-time price estimation display
- [ ] Booking creation submits and shows success
- [ ] Validation: past dates, end before start, missing price → error messages
- [ ] My Bookings screen with role toggle (renter/owner)
- [ ] Booking cards with status badges
- [ ] Status filter tabs work
- [ ] Booking detail screen shows full info
- [ ] Owner can accept/decline from detail screen
- [ ] Either party can cancel with reason
- [ ] "Mark as Paid" works for confirmed bookings
- [ ] "Go to Chat" navigates to the thread
- [ ] Confirmation dialogs before destructive actions
- [ ] Pull to refresh on bookings list
- [ ] Git commit: `feat(bookings): Wave 03 — Bookings complete`
