# TERMINAL MOBILE — WAVE 01: AUTHENTICATION
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 00 must be complete before starting this wave.

---

## Context

This wave implements the full authentication flow: register, login, phone OTP verification, password reset, and persistent sessions. After this wave, users can create accounts, verify their phones, log in, and stay logged in across app restarts.

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/register/` | Create account |
| `POST` | `/api/v1/auth/login/` | Get JWT tokens |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh access token |
| `POST` | `/api/v1/auth/logout/` | Blacklist refresh token |
| `POST` | `/api/v1/auth/verify-phone/` | Verify phone OTP |
| `POST` | `/api/v1/auth/resend-otp/` | Resend phone OTP |
| `POST` | `/api/v1/auth/password/reset/` | Request password reset |
| `POST` | `/api/v1/auth/password/reset/confirm/` | Confirm reset with OTP |
| `GET` | `/api/v1/users/me/` | Fetch user profile |

---

## Step 1: API functions

**File: `src/api/auth.ts`**

```typescript
import { apiClient } from './client';

export const authApi = {
  register: (data: {
    email: string;
    phone: string;
    first_name: string;
    last_name: string;
    password: string;
    password_confirm: string;
  }) => apiClient.post('/auth/register/', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post('/auth/login/', data),

  refreshToken: (refresh: string) =>
    apiClient.post('/auth/token/refresh/', { refresh }),

  logout: (refresh: string) =>
    apiClient.post('/auth/logout/', { refresh }),

  verifyPhone: (otp_code: string) =>
    apiClient.post('/auth/verify-phone/', { otp_code }),

  resendOtp: () =>
    apiClient.post('/auth/resend-otp/'),

  requestPasswordReset: (email: string) =>
    apiClient.post('/auth/password/reset/', { email }),

  confirmPasswordReset: (data: {
    email: string;
    otp_code: string;
    new_password: string;
  }) => apiClient.post('/auth/password/reset/confirm/', data),

  getMe: () => apiClient.get('/users/me/'),
};
```

---

## Step 2: Validation schemas

**File: `src/utils/validation.ts`**

```typescript
import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

export const registerSchema = z.object({
  first_name: z.string().min(2, 'First name is required'),
  last_name: z.string().min(2, 'Last name is required'),
  email: z.string().email('Enter a valid email'),
  phone: z.string().min(10, 'Enter a valid phone number'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  password_confirm: z.string(),
}).refine((data) => data.password === data.password_confirm, {
  message: 'Passwords do not match',
  path: ['password_confirm'],
});

export const otpSchema = z.object({
  otp_code: z.string().length(6, 'OTP must be 6 digits'),
});

export const forgotPasswordSchema = z.object({
  email: z.string().email('Enter a valid email'),
});

export const resetPasswordSchema = z.object({
  email: z.string().email(),
  otp_code: z.string().length(6, 'OTP must be 6 digits'),
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type OtpFormData = z.infer<typeof otpSchema>;
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
```

---

## Step 3: Screens

### Login Screen (`app/(auth)/login.tsx`)

**UI requirements:**
- Terminal logo at top
- Email input field
- Password input field (with show/hide toggle)
- "Log In" button (primary, full width)
- "Forgot password?" link
- "Don't have an account? Register" link at bottom
- Loading state on button while API call is in progress
- Error toast/alert on failure

**Flow:**
1. User enters email + password
2. Submit → `POST /api/v1/auth/login/`
3. Response: `{ access, refresh }`
4. Store tokens via `useAuthStore.setTokens()`
5. Fetch profile: `GET /api/v1/users/me/` → `useAuthStore.setUser()`
6. If `is_phone_verified === false` → navigate to `verify-phone`
7. Else → navigate to `(tabs)`

### Register Screen (`app/(auth)/register.tsx`)

**UI requirements:**
- First name, Last name inputs
- Email input
- Phone input (with +234 prefix)
- Password + Confirm password inputs
- "Create Account" button
- "Already have an account? Log in" link

**Flow:**
1. Validate with `registerSchema`
2. Submit → `POST /api/v1/auth/register/`
3. Response includes tokens: store them
4. Navigate to `verify-phone`

### Verify Phone Screen (`app/(auth)/verify-phone.tsx`)

**UI requirements:**
- Instructional text: "Enter the 6-digit code sent to your phone"
- 6-digit OTP input (individual boxes or single input)
- "Verify" button
- "Resend code" link (with 60s cooldown timer)

**Flow:**
1. User enters 6-digit code
2. Submit → `POST /api/v1/auth/verify-phone/`
3. On success → fetch profile → navigate to `(tabs)`
4. "Resend" → `POST /api/v1/auth/resend-otp/`

### Forgot Password Screen (`app/(auth)/forgot-password.tsx`)

**UI requirements:**
- Email input
- "Send Reset Code" button
- Back arrow to login

**Flow:**
1. Submit → `POST /api/v1/auth/password/reset/`
2. Navigate to `reset-password` screen with email pre-filled

### Reset Password Screen (`app/(auth)/reset-password.tsx`)

**UI requirements:**
- OTP input (6 digits)
- New password input
- "Reset Password" button

**Flow:**
1. Submit → `POST /api/v1/auth/password/reset/confirm/`
2. On success → navigate to login with success toast

---

## Step 4: Auth gate in root layout

Update `app/_layout.tsx`:
- On mount: call `hydrate()`
- If loading → show splash/loading screen
- If authenticated → render `(tabs)` layout
- If not authenticated → render `(auth)` layout

---

## Step 5: Logout

Add to profile screen:
- "Log Out" button
- On press: `POST /api/v1/auth/logout/` with refresh token → `clearAuth()` → redirect to login

---

## Definition of Done

- [ ] Login screen renders, submits credentials, stores JWT tokens, fetches profile
- [ ] Register screen validates form, creates account, navigates to OTP
- [ ] Verify phone screen accepts 6-digit OTP, verifies, navigates to main app
- [ ] Resend OTP works with cooldown timer
- [ ] Forgot password → enter email → receive OTP → reset password → login
- [ ] Tokens persist across app restarts (SecureStore)
- [ ] Auto-refresh on 401 works transparently
- [ ] Auth gate redirects unauthenticated users to login
- [ ] Logout clears tokens and redirects to login
- [ ] Form validation shows inline errors
- [ ] Loading states on all buttons during API calls
- [ ] Error handling shows user-friendly messages
- [ ] Git commit: `feat(auth): Wave 01 — Authentication complete`
