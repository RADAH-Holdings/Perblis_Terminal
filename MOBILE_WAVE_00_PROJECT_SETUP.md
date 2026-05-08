# TERMINAL MOBILE — WAVE 00: PROJECT SETUP
> Agent task file. Execute every instruction in order. Do not skip steps.
> This wave creates the foundation for the Terminal React Native mobile app.

---

## Context

Terminal Mobile is a React Native (Expo) app that interfaces with the Terminal REST API backend. The backend is deployed and documented at its Swagger endpoint. This wave establishes the project skeleton, navigation architecture, API client, state management, and design tokens.

**Tech stack decisions (do not deviate):**
- **Framework**: React Native with Expo (SDK 52+, managed workflow)
- **Navigation**: Expo Router (file-based routing)
- **State management**: Zustand (lightweight, no boilerplate)
- **API client**: Axios with interceptors for JWT refresh
- **Realtime**: Ably React Native SDK
- **Maps**: react-native-maps (Google Maps on Android, Apple Maps on iOS)
- **Forms**: React Hook Form + Zod validation
- **Storage**: expo-secure-store (tokens), @react-native-async-storage/async-storage (preferences)
- **Styling**: NativeWind (Tailwind CSS for React Native) OR StyleSheet — match the design system
- **Image handling**: expo-image-picker, expo-image

---

## Step 1: Initialize the Expo project

```bash
npx create-expo-app@latest terminal-mobile --template tabs
cd terminal-mobile
```

---

## Step 2: Install core dependencies

```bash
# Navigation (Expo Router already included with tabs template)
npx expo install expo-router expo-linking expo-constants

# State & storage
npm install zustand
npx expo install @react-native-async-storage/async-storage expo-secure-store

# API & networking
npm install axios

# Forms & validation
npm install react-hook-form zod @hookform/resolvers

# Maps
npx expo install react-native-maps expo-location

# Media
npx expo install expo-image-picker expo-image expo-file-system

# Realtime
npm install ably

# UI utilities
npx expo install expo-haptics expo-blur expo-linear-gradient

# Date handling
npm install date-fns
```

---

## Step 3: Create the directory structure

```
app/
├── (auth)/                    # Auth group (no bottom tabs)
│   ├── _layout.tsx
│   ├── login.tsx
│   ├── register.tsx
│   ├── verify-phone.tsx
│   ├── forgot-password.tsx
│   └── reset-password.tsx
├── (tabs)/                    # Main app (bottom tab navigation)
│   ├── _layout.tsx
│   ├── index.tsx              # Home / Map search
│   ├── bookings.tsx           # My bookings
│   ├── messages.tsx           # Chat threads
│   ├── listings.tsx           # My listings (owner)
│   └── profile.tsx            # Profile & settings
├── listing/
│   └── [id].tsx               # Listing detail
├── booking/
│   └── [id].tsx               # Booking detail
├── thread/
│   └── [id].tsx               # Chat thread detail
├── _layout.tsx                # Root layout
└── +not-found.tsx
src/
├── api/
│   ├── client.ts              # Axios instance + interceptors
│   ├── auth.ts                # Auth API calls
│   ├── listings.ts            # Listings API calls
│   ├── search.ts              # Search API calls
│   ├── bookings.ts            # Bookings API calls
│   └── messaging.ts           # Messaging API calls
├── stores/
│   ├── auth.store.ts          # Auth state (user, tokens)
│   ├── bookings.store.ts      # Bookings state
│   └── messaging.store.ts     # Threads & messages state
├── hooks/
│   ├── useAuth.ts
│   ├── useLocation.ts
│   └── useAbly.ts
├── components/
│   ├── ui/                    # Reusable UI primitives
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Avatar.tsx
│   │   ├── Badge.tsx
│   │   ├── BottomSheet.tsx
│   │   └── LoadingSpinner.tsx
│   ├── listings/
│   │   ├── ListingCard.tsx
│   │   ├── ListingMap.tsx
│   │   └── MediaGallery.tsx
│   ├── bookings/
│   │   ├── BookingCard.tsx
│   │   └── BookingStatusBadge.tsx
│   └── messaging/
│       ├── ThreadCard.tsx
│       ├── MessageBubble.tsx
│       └── ChatInput.tsx
├── constants/
│   ├── colors.ts              # Design tokens: colors
│   ├── typography.ts          # Font sizes, weights, families
│   ├── spacing.ts             # Spacing scale
│   └── api.ts                 # API base URL, endpoints
├── types/
│   ├── auth.ts
│   ├── listing.ts
│   ├── booking.ts
│   ├── messaging.ts
│   └── api.ts                 # Generic API response types
└── utils/
    ├── format.ts              # Currency, date formatters
    ├── validation.ts          # Zod schemas
    └── storage.ts             # Secure storage helpers
```

---

## Step 4: Design tokens

**File: `src/constants/colors.ts`**

```typescript
export const colors = {
  // Primary — Terminal brand (sky blue)
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
    950: '#082f49',
  },
  // Neutrals
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
    950: '#030712',
  },
  // Semantic
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
  // Background
  background: '#ffffff',
  surface: '#f9fafb',
  // Text
  text: {
    primary: '#111827',
    secondary: '#6b7280',
    tertiary: '#9ca3af',
    inverse: '#ffffff',
  },
} as const;
```

**File: `src/constants/typography.ts`**

```typescript
export const typography = {
  h1: { fontSize: 28, fontWeight: '700' as const, lineHeight: 34 },
  h2: { fontSize: 22, fontWeight: '700' as const, lineHeight: 28 },
  h3: { fontSize: 18, fontWeight: '600' as const, lineHeight: 24 },
  body: { fontSize: 16, fontWeight: '400' as const, lineHeight: 22 },
  bodySmall: { fontSize: 14, fontWeight: '400' as const, lineHeight: 20 },
  caption: { fontSize: 12, fontWeight: '400' as const, lineHeight: 16 },
  button: { fontSize: 16, fontWeight: '600' as const, lineHeight: 22 },
  label: { fontSize: 14, fontWeight: '500' as const, lineHeight: 18 },
} as const;
```

**File: `src/constants/spacing.ts`**

```typescript
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
  '4xl': 40,
  '5xl': 48,
} as const;

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
} as const;
```

---

## Step 5: API client with JWT interceptors

**File: `src/api/client.ts`**

```typescript
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = __DEV__
  ? 'http://localhost:8000'
  : 'https://your-production-url.railway.app';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Request interceptor: attach access token
apiClient.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: auto-refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await SecureStore.getItemAsync('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post(
          `${API_BASE_URL}/api/v1/auth/token/refresh/`,
          { refresh: refreshToken }
        );

        await SecureStore.setItemAsync('access_token', data.access);
        if (data.refresh) {
          await SecureStore.setItemAsync('refresh_token', data.refresh);
        }

        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed — clear tokens and redirect to login
        await SecureStore.deleteItemAsync('access_token');
        await SecureStore.deleteItemAsync('refresh_token');
        // Trigger auth state reset (handled by store subscription)
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

---

## Step 6: Auth store (Zustand)

**File: `src/stores/auth.store.ts`**

```typescript
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  profile_photo: string | null;
  bio: string;
  is_owner: boolean;
  is_renter: boolean;
  verification_level: number;
  is_phone_verified: boolean;
  is_email_verified: boolean;
  is_id_verified: boolean;
  unread_messages: number;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => Promise<void>;
  clearAuth: () => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => set({ user, isAuthenticated: true }),

  setTokens: async (access, refresh) => {
    await SecureStore.setItemAsync('access_token', access);
    await SecureStore.setItemAsync('refresh_token', refresh);
    set({ isAuthenticated: true });
  },

  clearAuth: async () => {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  hydrate: async () => {
    const token = await SecureStore.getItemAsync('access_token');
    set({ isAuthenticated: !!token, isLoading: false });
  },
}));
```

---

## Step 7: Type definitions

**File: `src/types/api.ts`**

```typescript
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: Record<string, string[]> | string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  count: number;
  data: T[];
}
```

**File: `src/types/listing.ts`**

```typescript
export type ResourceType = 'equipment' | 'vehicle' | 'warehouse' | 'terminal' | 'facility';
export type ListingStatus = 'draft' | 'active' | 'paused' | 'archived';

export interface ListingOwner {
  id: string;
  full_name: string;
  profile_photo: string | null;
  verification_level: number;
}

export interface ListingMedia {
  id: string;
  file: string;
  is_primary: boolean;
  display_order: number;
}

export interface Listing {
  id: string;
  owner: ListingOwner;
  resource_type: ResourceType;
  title: string;
  description: string;
  category: string;
  price_daily: string | null;
  price_weekly: string | null;
  price_monthly: string | null;
  specs: Record<string, any>;
  latitude: number | null;
  longitude: number | null;
  location_address: string;
  location_city: string;
  operator_available: boolean;
  delivery_available: boolean;
  status: ListingStatus;
  is_available: boolean;
  verification_tier: string;
  view_count: number;
  primary_photo_url: string | null;
  media: ListingMedia[];
  created_at: string;
  updated_at: string;
}

export interface SearchResult extends Listing {
  distance_km: number;
}
```

**File: `src/types/booking.ts`**

```typescript
export type BookingStatus = 'pending' | 'confirmed' | 'declined' | 'active' | 'completed' | 'cancelled';
export type PaymentStatus = 'unpaid' | 'simulated_paid';
export type DurationType = 'daily' | 'weekly' | 'monthly';

export interface BookingParty {
  id: string;
  full_name: string;
  profile_photo: string | null;
  phone: string;
}

export interface Booking {
  id: string;
  renter: BookingParty;
  owner: BookingParty;
  listing_id: string;
  listing_title: string;
  start_date: string;
  end_date: string;
  duration_type: DurationType;
  duration_days: number;
  gross_amount: string;
  commission_rate: string;
  commission_amount: string;
  owner_payout_amount: string;
  renter_note: string;
  status: BookingStatus;
  payment_status: PaymentStatus;
  cancellation_reason: string;
  thread_id: string | null;
  created_at: string;
  updated_at: string;
}
```

**File: `src/types/messaging.ts`**

```typescript
export interface MessageSender {
  id: string;
  full_name: string;
  profile_photo: string | null;
}

export interface Message {
  id: string;
  sender: MessageSender;
  body: string;
  is_read: boolean;
  created_at: string;
}

export interface ThreadParticipant {
  id: string;
  full_name: string;
  profile_photo: string | null;
}

export interface LastMessage {
  body: string;
  sender_name: string;
  created_at: string;
}

export interface Thread {
  id: string;
  is_booking_thread: boolean;
  booking_id: string | null;
  listing_title: string | null;
  other_participant: ThreadParticipant | null;
  last_message: LastMessage | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
}
```

---

## Step 8: Utility formatters

**File: `src/utils/format.ts`**

```typescript
export function formatCurrency(amount: string | number): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return `₦${num.toLocaleString('en-NG', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-NG', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function formatRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}
```

---

## Step 9: Root layout with auth gate

**File: `app/_layout.tsx`** — wrap in auth provider, redirect to login if unauthenticated.

The root layout should:
1. Call `useAuthStore.hydrate()` on mount
2. Show a splash screen while loading
3. Redirect to `(auth)/login` if not authenticated
4. Redirect to `(tabs)` if authenticated

---

## Step 10: Verify the skeleton runs

```bash
npx expo start
```

Ensure:
- App loads on iOS simulator and/or Android emulator
- Navigation between tabs works
- No TypeScript errors

---

## Definition of Done

- [ ] Expo project initialised with TypeScript
- [ ] All dependencies installed (no errors on `npx expo start`)
- [ ] Directory structure created as specified
- [ ] Design tokens defined (colors, typography, spacing)
- [ ] API client with JWT interceptor working
- [ ] Auth store with hydration logic
- [ ] Type definitions for all API entities
- [ ] Root layout with auth gate (redirect to login if no token)
- [ ] Bottom tab navigation renders with placeholder screens
- [ ] App compiles and runs on at least one platform (iOS or Android)
- [ ] Git commit: `chore: Wave 00 — Project setup complete`
