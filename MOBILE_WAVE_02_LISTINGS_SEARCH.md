# TERMINAL MOBILE — WAVE 02: LISTINGS & MAP SEARCH
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 01 must be complete before starting this wave.

---

## Context

This wave builds the core browsing experience: the interactive map-based search, listing detail view, listing creation (for owners), and media upload. After this wave, renters can discover assets near them and owners can publish their assets.

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/search/map/` | Proximity search (lat, lng, radius, filters) |
| `GET` | `/api/v1/listings/` | List user's own listings |
| `POST` | `/api/v1/listings/` | Create a new listing |
| `GET` | `/api/v1/listings/{id}/` | Listing detail (increments view_count) |
| `PUT/PATCH` | `/api/v1/listings/{id}/` | Update listing |
| `PATCH` | `/api/v1/listings/{id}/status/` | Change listing status (draft → active) |
| `POST` | `/api/v1/listings/{id}/media/` | Upload listing photo |
| `DELETE` | `/api/v1/listings/{id}/media/{media_id}/` | Remove photo |
| `POST` | `/api/v1/listings/{id}/report/` | Report a listing |

---

## Step 1: API functions

**File: `src/api/search.ts`**

```typescript
import { apiClient } from './client';

export interface SearchParams {
  lat: number;
  lng: number;
  radius?: number;
  resource_type?: string;
  min_price?: number;
  max_price?: number;
}

export const searchApi = {
  mapSearch: (params: SearchParams) =>
    apiClient.get('/search/map/', { params }),
};
```

**File: `src/api/listings.ts`**

```typescript
import { apiClient } from './client';

export const listingsApi = {
  getAll: () => apiClient.get('/listings/'),

  getById: (id: string) => apiClient.get(`/listings/${id}/`),

  create: (data: {
    title: string;
    resource_type: string;
    description?: string;
    category?: string;
    price_daily?: string;
    price_weekly?: string;
    price_monthly?: string;
    latitude?: number;
    longitude?: number;
    location_address?: string;
    location_city?: string;
    specs?: Record<string, any>;
    operator_available?: boolean;
    delivery_available?: boolean;
  }) => apiClient.post('/listings/', data),

  update: (id: string, data: Partial<any>) =>
    apiClient.patch(`/listings/${id}/`, data),

  updateStatus: (id: string, status: string) =>
    apiClient.patch(`/listings/${id}/status/`, { status }),

  uploadMedia: (id: string, formData: FormData) =>
    apiClient.post(`/listings/${id}/media/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  deleteMedia: (listingId: string, mediaId: string) =>
    apiClient.delete(`/listings/${listingId}/media/${mediaId}/`),

  report: (id: string, data: { reason: string; description?: string }) =>
    apiClient.post(`/listings/${id}/report/`, data),
};
```

---

## Step 2: Screens

### Home / Map Search Screen (`app/(tabs)/index.tsx`)

**This is the primary screen of the app.**

**UI requirements:**
- Full-screen map (react-native-maps) showing listing markers
- User's current location shown with a blue dot
- Map markers for each listing result (color-coded by resource_type)
- Tapping a marker shows a small card preview at bottom
- Pull-up bottom sheet with listing cards (scrollable list)
- Filter bar at top: resource type pills (Equipment, Vehicle, Warehouse, Terminal, Facility)
- Search radius defaults to 50km from user's current location

**Flow:**
1. On mount: request location permission → get current position
2. Call `GET /api/v1/search/map/?lat={lat}&lng={lng}&radius=50`
3. Render markers on map
4. On marker tap → show listing preview card
5. On card tap → navigate to `listing/[id]`
6. On filter change → re-fetch with `resource_type` param

**Marker colors by type:**
- Equipment: `#f59e0b` (amber)
- Vehicle: `#8b5cf6` (purple)
- Warehouse: `#10b981` (green)
- Terminal: `#3b82f6` (blue)
- Facility: `#ef4444` (red)

### Listing Detail Screen (`app/listing/[id].tsx`)

**UI requirements:**
- Photo gallery (horizontal scroll, dots indicator)
- Title, resource type badge, location
- Price section (daily / weekly / monthly — show all that exist)
- Owner info card (avatar, name, verification badge)
- Description section
- Specs section (key-value grid from JSON specs)
- Features badges: "Operator Available", "Delivery Available"
- Two action buttons at bottom:
  - "Book Now" → navigate to booking creation flow
  - "Send Inquiry" → create messaging thread
- "Report" option in header menu (⋮)

**Flow:**
1. Fetch `GET /api/v1/listings/{id}/`
2. Render all sections
3. "Book Now" → open booking bottom sheet (Wave 03)
4. "Send Inquiry" → `POST /api/v1/threads/` with initial message prompt

### My Listings Screen (`app/(tabs)/listings.tsx`) — Owner only

**UI requirements:**
- List of user's own listings (card format)
- Each card shows: title, status badge, photo, price, view count
- FAB button "+" to create new listing
- Tab filters: All, Active, Draft, Paused
- Empty state for no listings

**Flow:**
1. Fetch `GET /api/v1/listings/`
2. Render list
3. Tap card → navigate to listing detail (editable mode for owner)
4. FAB → navigate to create listing flow

### Create/Edit Listing Flow (multi-step)

**Screens (modal stack or step wizard):**

**Step 1 — Basic Info:**
- Resource type picker (5 options with icons)
- Title input
- Description (multiline)
- Category input

**Step 2 — Pricing:**
- Price daily (optional)
- Price weekly (optional)
- Price monthly (optional)
- Duration type info

**Step 3 — Location:**
- Map picker (tap to drop pin, or use current location)
- Address input
- City input

**Step 4 — Photos:**
- Photo grid (tap to add from camera/gallery)
- Set primary photo (tap star icon)
- Minimum 1 photo required before publishing

**Step 5 — Extras:**
- Operator available (toggle)
- Delivery available (toggle)
- Specs (add key-value pairs)

**Final action:**
- "Save as Draft" → create listing (status stays `draft`)
- "Publish" → create listing → `PATCH .../status/` with `{"status": "active"}`

---

## Step 3: Location hook

**File: `src/hooks/useLocation.ts`**

```typescript
import { useState, useEffect } from 'react';
import * as Location from 'expo-location';

export function useLocation() {
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setError('Location permission denied');
        // Default to Lagos
        setLocation({ lat: 6.5244, lng: 3.3792 });
        return;
      }
      const pos = await Location.getCurrentPositionAsync({});
      setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    })();
  }, []);

  return { location, error };
}
```

---

## Step 4: Listing card component

**File: `src/components/listings/ListingCard.tsx`**

Should display:
- Primary photo (or placeholder)
- Title (1 line, truncated)
- Resource type badge (colored)
- Location city
- Price (show lowest available: daily → weekly → monthly)
- Distance (if from search results)

---

## Definition of Done

- [ ] Map search screen renders with current location and listing markers
- [ ] Markers are color-coded by resource type
- [ ] Tapping marker shows listing preview card
- [ ] Filter bar filters results by resource type
- [ ] Listing detail screen shows all info: photos, price, specs, owner, location
- [ ] "Send Inquiry" from listing detail creates a thread (POST /api/v1/threads/)
- [ ] My Listings screen shows owner's listings with status badges
- [ ] Create listing flow (5 steps) creates a listing with media
- [ ] Photos can be uploaded from camera or gallery
- [ ] "Publish" sets listing status to active
- [ ] Empty states for no results / no listings
- [ ] Smooth map pan/zoom experience
- [ ] Git commit: `feat(listings): Wave 02 — Listings and map search complete`
