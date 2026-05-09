# TERMINAL MOBILE — WAVE 05: PROFILE, SETTINGS & POLISH
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 04 must be complete before starting this wave.
> This is the final wave. After this, Terminal Mobile MVP is ready for TestFlight / internal testing.

---

## Context

This wave completes the user profile, role management, KYC document upload, settings, and overall app polish. It also handles edge cases, error states, and visual refinement across all previous screens.

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/users/me/` | Fetch profile + unread count |
| `PUT/PATCH` | `/api/v1/users/me/` | Update profile |
| `PATCH` | `/api/v1/users/me/role/` | Toggle owner/renter role |
| `POST` | `/api/v1/users/me/documents/` | Upload KYC document |
| `POST` | `/api/v1/auth/password/change/` | Change password |
| `POST` | `/api/v1/auth/logout/` | Logout |
| `GET` | `/api/v1/users/{id}/` | View public profile |

---

## Step 1: Profile Screen (`app/(tabs)/profile.tsx`)

**UI requirements:**
- Profile header: large avatar (tap to change), full name, email
- Verification badges row:
  - ✓ Email verified (always, set during registration)
  - ✓/✗ Phone verified
  - ✓/✗ ID verified
  - Verification level indicator (0, 1, 2)
- Stats row: total bookings made, total bookings received, total listings
- Menu sections:

**Section: Account**
| Item | Icon | Action |
|---|---|---|
| Edit Profile | ✏️ | Navigate to edit profile screen |
| Change Password | 🔑 | Navigate to change password screen |
| Role Management | 👥 | Toggle owner/renter roles |
| KYC Verification | 📄 | Upload documents |

**Section: Preferences**
| Item | Icon | Action |
|---|---|---|
| Notifications | 🔔 | Toggle push notifications (stub) |
| Language | 🌐 | Language picker (stub — English only for MVP) |

**Section: About**
| Item | Icon | Action |
|---|---|---|
| Terms of Service | 📋 | Open in-app browser |
| Privacy Policy | 🔒 | Open in-app browser |
| App Version | ℹ️ | Display version number |

**Section: Danger Zone**
| Item | Icon | Action |
|---|---|---|
| Log Out | 🚪 | Confirm → logout |

---

## Step 2: Edit Profile Screen

**UI requirements:**
- Avatar with "Change Photo" overlay button
- First name input
- Last name input
- Phone input
- Bio (multiline)
- "Save Changes" button

**Flow:**
1. Pre-fill with current user data from store
2. On save: `PATCH /api/v1/users/me/` with changed fields
3. If photo changed: include `profile_photo` as multipart form data
4. On success → update store → show success toast → go back

---

## Step 3: Role Management Screen

**UI requirements:**
- Two toggle cards:
  - "I'm a Renter" — toggle switch (shows: "Browse and book assets")
  - "I'm an Owner" — toggle switch (shows: "List and manage assets")
- Rule: at least one must be active (show error if user tries to disable both)
- Explanation text: "Your role determines which features you see"

**Flow:**
1. Show current roles from `user.is_renter` / `user.is_owner`
2. On toggle: `PATCH /api/v1/users/me/role/` with updated values
3. Update store
4. If owner is now enabled → show "My Listings" tab in bottom nav
5. If owner is disabled → hide "My Listings" tab

---

## Step 4: KYC Document Upload Screen

**UI requirements:**
- Document type selector: "Government ID" | "Business Registration"
- File picker (camera or gallery)
- Preview of selected document image
- "Upload" button
- Status indicator after upload (shows "Verified ✓" — auto-approved in MVP)

**Flow:**
1. Select document type
2. Pick file from camera/gallery
3. Submit as multipart: `POST /api/v1/users/me/documents/`
4. On success → show "Verified" status → update user in store

---

## Step 5: Change Password Screen

**UI requirements:**
- Current password input
- New password input
- Confirm new password input
- "Change Password" button

**Flow:**
1. Validate: new password matches confirm, min 8 chars
2. Submit: `POST /api/v1/auth/password/change/`
3. On success → toast → go back
4. On error (wrong current password) → show inline error

---

## Step 6: Public Profile Screen (`app/user/[id].tsx`)

**UI requirements:**
- Avatar, full name
- Bio
- Verification badges
- Role badges (Owner / Renter)
- Member since date
- If the user is an owner: show their active listings count

**Flow:**
1. Fetch `GET /api/v1/users/{id}/`
2. Render public profile

---

## Step 7: Conditional tab visibility

Based on user roles:
- **Renters only** (is_renter=true, is_owner=false):
  - Tabs: Home, Bookings, Messages, Profile
- **Owners only** (is_owner=true, is_renter=false):
  - Tabs: Home, My Listings, Bookings, Messages, Profile
- **Both** (is_renter=true, is_owner=true):
  - Tabs: Home, My Listings, Bookings, Messages, Profile

The "My Listings" tab only appears if `is_owner === true`.

---

## Step 8: Global polish

### Loading states
- Every screen that fetches data shows a skeleton/shimmer loader
- Every button that triggers an API call shows a spinner

### Error states
- Network error → "No internet connection" banner (detect with NetInfo)
- 500 errors → "Something went wrong. Try again." with retry button
- 404 → "Not found" screen with back button
- Validation errors → inline below the relevant field

### Empty states
- No bookings → illustration + "No bookings yet" + CTA
- No listings → illustration + "List your first asset" + CTA
- No messages → illustration + "No conversations" + CTA
- No search results → "No assets found in this area" + suggestion

### Pull to refresh
- All list screens support pull-to-refresh

### Haptics
- Light haptic on button press
- Success haptic on successful action (booking created, message sent)
- Error haptic on validation failure

### Animations
- Screen transitions: native stack animations
- Bottom sheets: spring animation
- Cards: subtle scale on press (`Pressable` with `transform`)
- Tab bar: icon bounce on tap

---

## Step 9: App icon and splash screen

- Create app icon (use Terminal branding: sky blue gradient, "T" lettermark)
- Configure splash screen (Terminal logo centered, white/sky-blue background)
- Update `app.json`:
  ```json
  {
    "expo": {
      "name": "Terminal",
      "slug": "terminal-mobile",
      "scheme": "terminal",
      "icon": "./assets/icon.png",
      "splash": {
        "image": "./assets/splash.png",
        "resizeMode": "contain",
        "backgroundColor": "#0ea5e9"
      }
    }
  }
  ```

---

## Step 10: Final check and build

```bash
# Type check
npx tsc --noEmit

# Lint
npx eslint . --ext .ts,.tsx

# Test build
npx expo export --platform ios
npx expo export --platform android

# Preview build (for TestFlight / Play Store internal track)
npx eas build --platform ios --profile preview
npx eas build --platform android --profile preview
```

---

## Definition of Done

- [ ] Profile screen shows user info, stats, verification badges, menu
- [ ] Edit profile: change name, phone, bio, photo → saves successfully
- [ ] Role management: toggle owner/renter → tabs update accordingly
- [ ] KYC document upload works (camera/gallery → multipart upload)
- [ ] Change password flow works
- [ ] Public profile screen renders for other users
- [ ] "My Listings" tab appears/disappears based on owner role
- [ ] Skeleton loaders on all data-fetching screens
- [ ] Error states with retry buttons
- [ ] Empty states with illustrations and CTAs
- [ ] Pull to refresh on all list screens
- [ ] Haptic feedback on interactions
- [ ] App icon and splash screen configured
- [ ] No TypeScript errors (`tsc --noEmit`)
- [ ] App builds successfully for both platforms
- [ ] Git commit: `chore: Wave 05 — Profile, settings, and polish complete`
- [ ] Tag: `mvp-v1.0`

---

## Post-MVP Notes

| Feature | Status | Next Step |
|---|---|---|
| Push notifications | Stub only | Integrate expo-notifications + backend push |
| Real payments | Simulated | Paystack/Flutterwave SDK integration |
| Image caching | Basic | Add expo-image caching policies |
| Offline support | None | Add react-query offline persistence |
| Analytics | None | Mixpanel or Amplitude SDK |
| Deep linking | Schema defined | Wire up `terminal://` links |
| App Store submission | Preview build | Full production build + metadata |
