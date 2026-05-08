# TERMINAL MOBILE — WAVE 01: AUTHENTICATION
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 00 must be complete before starting this wave.
> Do not proceed to Wave 02 until the Definition of Done checklist is fully complete.

---

## Context

This wave builds the full authentication flow for the Terminal Mobile app — login, registration, and phone verification. The backend API already implements these endpoints (Django REST + SimpleJWT). This wave connects the mobile app to them.

**Backend endpoints consumed (all under `/api/v1/`):**

| Method | Path | Auth | Request body | Response |
|--------|------|------|-------------|----------|
| POST | `/auth/register/` | No | `{ email, phone, first_name, last_name, password, password_confirm }` | `{ success, message, tokens: { access, refresh }, user: { id, email, full_name, is_owner, is_renter } }` |
| POST | `/auth/login/` | No | `{ email, password }` | `{ access, refresh }` |
| POST | `/auth/verify-phone/` | Yes | `{ otp_code }` | `{ success, message }` |
| POST | `/auth/resend-otp/` | Yes | `{}` | `{ success, message }` |
| POST | `/auth/token/refresh/` | No | `{ refresh }` | `{ access }` |
| POST | `/auth/logout/` | Yes | `{ refresh }` | `{ success, message }` |
| GET | `/users/me/` | Yes | — | `{ success, data: User }` |

**Design system in effect:** Forge Dark (TDS v1.1). All token values from `src/theme/`.

**Voice rules (non-negotiable):**
- No emoji anywhere in user-facing copy
- No exclamation marks
- Imperative, terse — "dispatch, not customer service"
- Error messages must be actionable: tell the user what to do, not just what went wrong

---

## Step 1: Create the auth API module

**File: `src/api/auth.ts`**

```typescript
import apiClient from './client';
import type { AuthTokens, User } from './types';

// --- Request types ---

export interface RegisterRequest {
  email: string;
  phone: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface VerifyPhoneRequest {
  otp_code: string;
}

export interface RefreshTokenRequest {
  refresh: string;
}

export interface LogoutRequest {
  refresh: string;
}

// --- Response types ---

export interface RegisterResponse {
  success: boolean;
  message: string;
  tokens: AuthTokens;
  user: {
    id: string;
    email: string;
    full_name: string;
    is_owner: boolean;
    is_renter: boolean;
  };
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface VerifyPhoneResponse {
  success: boolean;
  message: string;
}

export interface ResendOtpResponse {
  success: boolean;
  message: string;
}

// --- API functions ---

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>('/auth/register/', data);
  return response.data;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/auth/login/', data);
  return response.data;
}

export async function verifyPhone(data: VerifyPhoneRequest): Promise<VerifyPhoneResponse> {
  const response = await apiClient.post<VerifyPhoneResponse>('/auth/verify-phone/', data);
  return response.data;
}

export async function resendOtp(): Promise<ResendOtpResponse> {
  const response = await apiClient.post<ResendOtpResponse>('/auth/resend-otp/');
  return response.data;
}

export async function refreshToken(data: RefreshTokenRequest): Promise<{ access: string }> {
  const response = await apiClient.post<{ access: string }>('/auth/token/refresh/', data);
  return response.data;
}

export async function logout(data: LogoutRequest): Promise<void> {
  await apiClient.post('/auth/logout/', data);
}
```

---

## Step 2: Create the users API module

**File: `src/api/users.ts`**

```typescript
import apiClient from './client';
import type { User } from './types';

export interface MeResponse {
  success: boolean;
  data: User;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  phone?: string;
  bio?: string;
}

export interface UpdateProfileResponse {
  success: boolean;
  message: string;
  data: User;
}

export async function fetchMe(): Promise<MeResponse> {
  const response = await apiClient.get<MeResponse>('/users/me/');
  return response.data;
}

export async function updateProfile(data: UpdateProfileRequest): Promise<UpdateProfileResponse> {
  const response = await apiClient.patch<UpdateProfileResponse>('/users/me/', data);
  return response.data;
}
```

---

## Step 3: Create form validation schemas

**File: `src/utils/validation.ts`**

```typescript
import { z } from 'zod';

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required.')
    .email('Enter a valid email address.'),
  password: z
    .string()
    .min(1, 'Password is required.'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    email: z
      .string()
      .min(1, 'Email is required.')
      .email('Enter a valid email address.'),
    phone: z
      .string()
      .min(1, 'Phone number is required.')
      .regex(
        /^0[789]\d{9}$/,
        'Enter a valid Nigerian phone number (e.g. 08012345678).'
      ),
    first_name: z
      .string()
      .min(1, 'First name is required.')
      .max(50, 'First name must be under 50 characters.'),
    last_name: z
      .string()
      .min(1, 'Last name is required.')
      .max(50, 'Last name must be under 50 characters.'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters.'),
    password_confirm: z
      .string()
      .min(1, 'Confirm your password.'),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: 'Passwords do not match.',
    path: ['password_confirm'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

export const verifyPhoneSchema = z.object({
  otp_code: z
    .string()
    .length(6, 'Enter the 6-digit code.')
    .regex(/^\d{6}$/, 'Code must be 6 digits.'),
});

export type VerifyPhoneFormData = z.infer<typeof verifyPhoneSchema>;
```

---

## Step 4: Create the useAuth hook

**File: `src/hooks/useAuth.ts`**

```typescript
import { useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { useAuthStore } from '../store/authStore';
import * as authApi from '../api/auth';
import { fetchMe } from '../api/users';
import type { LoginFormData, RegisterFormData } from '../utils/validation';

export function useAuth() {
  const { setUser, setTokens, clearAuth } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokens = await authApi.login(data);
      await setTokens({ access: tokens.access, refresh: tokens.refresh });

      const meResponse = await fetchMe();
      setUser(meResponse.data);
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Couldn't reach the server. Tap to retry.";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.register(data);
      await setTokens(response.tokens);
      setUser({
        id: response.user.id,
        email: response.user.email,
        full_name: response.user.full_name,
        is_owner: response.user.is_owner,
        is_renter: response.user.is_renter,
        phone: data.phone,
        first_name: data.first_name,
        last_name: data.last_name,
        profile_photo: null,
        bio: '',
        verification_level: 0,
        is_phone_verified: false,
        is_email_verified: true,
        is_id_verified: false,
        created_at: new Date().toISOString(),
      });
    } catch (err: any) {
      const errors = err.response?.data?.errors || err.response?.data;
      if (typeof errors === 'object' && errors !== null) {
        const firstKey = Object.keys(errors)[0];
        const firstError = Array.isArray(errors[firstKey])
          ? errors[firstKey][0]
          : errors[firstKey];
        setError(String(firstError));
      } else {
        setError("Couldn't reach the server. Tap to retry.");
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyPhone = async (otpCode: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.verifyPhone({ otp_code: otpCode });
      const meResponse = await fetchMe();
      setUser(meResponse.data);
    } catch (err: any) {
      const message =
        err.response?.data?.errors?.otp_code ||
        err.response?.data?.message ||
        'Invalid or expired code. Request a new one.';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError(null);
    try {
      await authApi.resendOtp();
    } catch {
      setError("Couldn't send a new code. Tap to retry.");
    }
  };

  const handleLogout = async () => {
    try {
      const refreshToken = await SecureStore.getItemAsync('refresh_token');
      if (refreshToken) {
        await authApi.logout({ refresh: refreshToken });
      }
    } catch {
      // Logout is best-effort
    } finally {
      await clearAuth();
    }
  };

  return {
    isLoading,
    error,
    setError,
    handleLogin,
    handleRegister,
    handleVerifyPhone,
    handleResendOtp,
    handleLogout,
  };
}
```

---

## Step 5: Create shared form components

Before building screens, ensure `src/components/Input.tsx` and `src/components/Button.tsx` are fully implemented. If Wave 00 left them as placeholders, replace them now.

**File: `src/components/Input.tsx`**

```tsx
import React, { forwardRef, useState } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  type TextInputProps,
} from 'react-native';
import { colors } from '../theme/colors';
import { typeScale } from '../theme/typography';
import { spacing, radii } from '../theme/spacing';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  prefix?: string;
}

export const Input = forwardRef<TextInput, InputProps>(
  ({ label, error, prefix, style, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    return (
      <View style={styles.container}>
        {label && <Text style={styles.label}>{label}</Text>}
        <View
          style={[
            styles.inputWrapper,
            isFocused && styles.inputWrapperFocused,
            error ? styles.inputWrapperError : undefined,
          ]}
        >
          {prefix && <Text style={styles.prefix}>{prefix}</Text>}
          <TextInput
            ref={ref}
            style={[styles.input, prefix ? styles.inputWithPrefix : undefined, style]}
            placeholderTextColor={colors.textTertiary}
            selectionColor={colors.forge}
            cursorColor={colors.forge}
            onFocus={(e) => {
              setIsFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              props.onBlur?.(e);
            }}
            {...props}
          />
        </View>
        {error && <Text style={styles.error}>{error}</Text>}
      </View>
    );
  }
);

Input.displayName = 'Input';

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.base,
  },
  label: {
    ...typeScale.caption,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.default,
    height: 48,
    paddingHorizontal: spacing.md,
  },
  inputWrapperFocused: {
    borderColor: colors.forge,
  },
  inputWrapperError: {
    borderColor: colors.alert,
  },
  prefix: {
    ...typeScale.body1,
    color: colors.textSecondary,
    marginRight: spacing.xs,
  },
  input: {
    flex: 1,
    ...typeScale.body1,
    color: colors.textPrimary,
    height: '100%',
    padding: 0,
  },
  inputWithPrefix: {
    paddingLeft: 0,
  },
  error: {
    ...typeScale.body2,
    color: colors.alert,
    marginTop: spacing.xs,
  },
});
```

**File: `src/components/Button.tsx`**

```tsx
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  type ViewStyle,
  type TextStyle,
} from 'react-native';
import { colors } from '../theme/colors';
import { typeScale } from '../theme/typography';
import { radii } from '../theme/spacing';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  isLoading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  isLoading = false,
  disabled = false,
  style,
  textStyle,
}: ButtonProps) {
  const isDisabled = disabled || isLoading;

  return (
    <TouchableOpacity
      style={[
        styles.base,
        variant === 'primary' && styles.primary,
        variant === 'secondary' && styles.secondary,
        variant === 'ghost' && styles.ghost,
        isDisabled && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.8}
    >
      {isLoading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'primary' ? colors.textOnAccent : colors.forge}
        />
      ) : (
        <Text
          style={[
            styles.text,
            variant === 'primary' && styles.primaryText,
            variant === 'secondary' && styles.secondaryText,
            variant === 'ghost' && styles.ghostText,
            textStyle,
          ]}
        >
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    height: 44,
    borderRadius: radii.default,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  primary: {
    backgroundColor: colors.forge,
  },
  secondary: {
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.border,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    ...typeScale.h2,
  },
  primaryText: {
    color: colors.textOnAccent,
  },
  secondaryText: {
    color: colors.textPrimary,
  },
  ghostText: {
    color: colors.forge,
  },
});
```

---

## Step 6: Create the LoginScreen

**File: `src/screens/auth/LoginScreen.tsx`**

```tsx
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { useAuth } from '../../hooks/useAuth';
import { loginSchema, type LoginFormData } from '../../utils/validation';
import { colors } from '../../theme/colors';
import { typeScale } from '../../theme/typography';
import { spacing, screenPadding } from '../../theme/spacing';
import type { AuthStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AuthStackParamList, 'Login'>;

export function LoginScreen({ navigation }: Props) {
  const { handleLogin, isLoading, error, setError } = useAuth();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await handleLogin(data);
    } catch {
      // Error is set in useAuth
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={styles.heading}>SIGN IN</Text>
            <Text style={styles.subtitle}>
              Enter your credentials to continue.
            </Text>
          </View>

          {error && (
            <TouchableOpacity
              style={styles.errorBanner}
              onPress={() => setError(null)}
            >
              <Text style={styles.errorText}>{error}</Text>
            </TouchableOpacity>
          )}

          <View style={styles.form}>
            <Controller
              control={control}
              name="email"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="EMAIL"
                  placeholder="operator@company.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  returnKeyType="next"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.email?.message}
                />
              )}
            />

            <Controller
              control={control}
              name="password"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="PASSWORD"
                  placeholder="Enter password"
                  secureTextEntry
                  autoComplete="password"
                  returnKeyType="go"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.password?.message}
                />
              )}
            />

            <Button
              title="Request booking"
              onPress={handleSubmit(onSubmit)}
              isLoading={isLoading}
              style={styles.submitButton}
            />
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>No account yet?</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Register')}>
              <Text style={styles.footerLink}> Register</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.abyss,
  },
  flex: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: screenPadding.horizontal,
    justifyContent: 'center',
  },
  header: {
    marginBottom: spacing['2xl'],
  },
  heading: {
    ...typeScale.display3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subtitle: {
    ...typeScale.body1,
    color: colors.textSecondary,
  },
  errorBanner: {
    backgroundColor: colors.bgTintedDanger,
    borderRadius: 4,
    padding: spacing.md,
    marginBottom: spacing.base,
  },
  errorText: {
    ...typeScale.body2,
    color: colors.alertSoft,
  },
  form: {
    gap: spacing.xs,
  },
  submitButton: {
    marginTop: spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: spacing['2xl'],
  },
  footerText: {
    ...typeScale.body1,
    color: colors.textSecondary,
  },
  footerLink: {
    ...typeScale.body1,
    color: colors.forge,
  },
});
```

---

## Step 7: Create the RegisterScreen

**File: `src/screens/auth/RegisterScreen.tsx`**

```tsx
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { Input } from '../../components/Input';
import { Button } from '../../components/Button';
import { useAuth } from '../../hooks/useAuth';
import { registerSchema, type RegisterFormData } from '../../utils/validation';
import { colors } from '../../theme/colors';
import { typeScale } from '../../theme/typography';
import { spacing, screenPadding } from '../../theme/spacing';
import type { AuthStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AuthStackParamList, 'Register'>;

export function RegisterScreen({ navigation }: Props) {
  const { handleRegister, isLoading, error, setError } = useAuth();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      phone: '',
      first_name: '',
      last_name: '',
      password: '',
      password_confirm: '',
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await handleRegister(data);
      navigation.replace('VerifyPhone');
    } catch {
      // Error is set in useAuth
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={styles.heading}>CREATE ACCOUNT</Text>
            <Text style={styles.subtitle}>
              Set up your Terminal account to start leasing.
            </Text>
          </View>

          {error && (
            <TouchableOpacity
              style={styles.errorBanner}
              onPress={() => setError(null)}
            >
              <Text style={styles.errorText}>{error}</Text>
            </TouchableOpacity>
          )}

          <View style={styles.form}>
            <Controller
              control={control}
              name="first_name"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="FIRST NAME"
                  placeholder="First name"
                  autoCapitalize="words"
                  autoComplete="given-name"
                  returnKeyType="next"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.first_name?.message}
                />
              )}
            />

            <Controller
              control={control}
              name="last_name"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="LAST NAME"
                  placeholder="Last name"
                  autoCapitalize="words"
                  autoComplete="family-name"
                  returnKeyType="next"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.last_name?.message}
                />
              )}
            />

            <Controller
              control={control}
              name="email"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="EMAIL"
                  placeholder="operator@company.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  returnKeyType="next"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.email?.message}
                />
              )}
            />

            <Controller
              control={control}
              name="phone"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="PHONE"
                  placeholder="08012345678"
                  prefix="+234"
                  keyboardType="phone-pad"
                  autoComplete="tel"
                  returnKeyType="next"
                  maxLength={11}
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.phone?.message}
                />
              )}
            />

            <Controller
              control={control}
              name="password"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="PASSWORD"
                  placeholder="Minimum 8 characters"
                  secureTextEntry
                  autoComplete="new-password"
                  returnKeyType="next"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.password?.message}
                />
              )}
            />

            <Controller
              control={control}
              name="password_confirm"
              render={({ field: { onChange, onBlur, value } }) => (
                <Input
                  label="CONFIRM PASSWORD"
                  placeholder="Re-enter password"
                  secureTextEntry
                  autoComplete="new-password"
                  returnKeyType="go"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.password_confirm?.message}
                />
              )}
            />

            <Button
              title="Create account"
              onPress={handleSubmit(onSubmit)}
              isLoading={isLoading}
              style={styles.submitButton}
            />
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Already have an account?</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Login')}>
              <Text style={styles.footerLink}> Sign in</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.abyss,
  },
  flex: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: screenPadding.horizontal,
    paddingVertical: spacing['2xl'],
  },
  header: {
    marginBottom: spacing.xl,
  },
  heading: {
    ...typeScale.display3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subtitle: {
    ...typeScale.body1,
    color: colors.textSecondary,
  },
  errorBanner: {
    backgroundColor: colors.bgTintedDanger,
    borderRadius: 4,
    padding: spacing.md,
    marginBottom: spacing.base,
  },
  errorText: {
    ...typeScale.body2,
    color: colors.alertSoft,
  },
  form: {
    gap: spacing.xs,
  },
  submitButton: {
    marginTop: spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: spacing.xl,
    paddingBottom: spacing.xl,
  },
  footerText: {
    ...typeScale.body1,
    color: colors.textSecondary,
  },
  footerLink: {
    ...typeScale.body1,
    color: colors.forge,
  },
});
```

---

## Step 8: Create the VerifyPhoneScreen

**File: `src/screens/auth/VerifyPhoneScreen.tsx`**

```tsx
import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { Button } from '../../components/Button';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';
import { colors } from '../../theme/colors';
import { typeScale, fontFamilies } from '../../theme/typography';
import { spacing, radii, screenPadding } from '../../theme/spacing';
import type { AuthStackParamList } from '../../navigation/types';

const OTP_LENGTH = 6;

type Props = NativeStackScreenProps<AuthStackParamList, 'VerifyPhone'>;

export function VerifyPhoneScreen({ navigation }: Props) {
  const { handleVerifyPhone, handleResendOtp, isLoading, error, setError } =
    useAuth();
  const user = useAuthStore((s) => s.user);

  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const [resendCooldown, setResendCooldown] = useState(0);
  const inputRefs = useRef<(TextInput | null)[]>([]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleDigitChange = (text: string, index: number) => {
    if (text.length > 1) {
      // Handle paste: distribute digits across boxes
      const pasted = text.replace(/\D/g, '').slice(0, OTP_LENGTH);
      const newDigits = [...digits];
      for (let i = 0; i < pasted.length; i++) {
        if (index + i < OTP_LENGTH) {
          newDigits[index + i] = pasted[i];
        }
      }
      setDigits(newDigits);
      const nextIndex = Math.min(index + pasted.length, OTP_LENGTH - 1);
      inputRefs.current[nextIndex]?.focus();
      return;
    }

    const newDigits = [...digits];
    newDigits[index] = text.replace(/\D/g, '');
    setDigits(newDigits);

    if (text && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyPress = (key: string, index: number) => {
    if (key === 'Backspace' && !digits[index] && index > 0) {
      const newDigits = [...digits];
      newDigits[index - 1] = '';
      setDigits(newDigits);
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleSubmit = async () => {
    const code = digits.join('');
    if (code.length !== OTP_LENGTH) return;
    try {
      await handleVerifyPhone(code);
    } catch {
      // Error is set in useAuth
    }
  };

  const handleResend = async () => {
    await handleResendOtp();
    setResendCooldown(60);
  };

  const isComplete = digits.every((d) => d !== '');

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.heading}>VERIFY PHONE</Text>
            <Text style={styles.subtitle}>
              Enter the 6-digit code sent to{' '}
              <Text style={styles.phone}>{user?.phone ?? 'your phone'}</Text>.
            </Text>
            <Text style={styles.hint}>
              Check the server console for the OTP code.
            </Text>
          </View>

          {error && (
            <TouchableOpacity
              style={styles.errorBanner}
              onPress={() => setError(null)}
            >
              <Text style={styles.errorText}>{error}</Text>
            </TouchableOpacity>
          )}

          <View style={styles.otpRow}>
            {digits.map((digit, index) => (
              <TextInput
                key={index}
                ref={(ref) => {
                  inputRefs.current[index] = ref;
                }}
                style={[
                  styles.otpBox,
                  digit ? styles.otpBoxFilled : undefined,
                ]}
                value={digit}
                onChangeText={(text) => handleDigitChange(text, index)}
                onKeyPress={({ nativeEvent }) =>
                  handleKeyPress(nativeEvent.key, index)
                }
                keyboardType="number-pad"
                maxLength={index === 0 ? OTP_LENGTH : 1}
                selectTextOnFocus
                caretHidden
              />
            ))}
          </View>

          <Button
            title="Verify"
            onPress={handleSubmit}
            isLoading={isLoading}
            disabled={!isComplete}
            style={styles.submitButton}
          />

          <View style={styles.resendRow}>
            {resendCooldown > 0 ? (
              <Text style={styles.resendCooldownText}>
                Resend available in {resendCooldown}s
              </Text>
            ) : (
              <TouchableOpacity onPress={handleResend}>
                <Text style={styles.resendText}>Resend code</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.abyss,
  },
  flex: {
    flex: 1,
  },
  container: {
    flex: 1,
    paddingHorizontal: screenPadding.horizontal,
    justifyContent: 'center',
  },
  header: {
    marginBottom: spacing['2xl'],
  },
  heading: {
    ...typeScale.display3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subtitle: {
    ...typeScale.body1,
    color: colors.textSecondary,
  },
  phone: {
    color: colors.textPrimary,
  },
  hint: {
    ...typeScale.body2,
    color: colors.textTertiary,
    marginTop: spacing.xs,
  },
  errorBanner: {
    backgroundColor: colors.bgTintedDanger,
    borderRadius: 4,
    padding: spacing.md,
    marginBottom: spacing.base,
  },
  errorText: {
    ...typeScale.body2,
    color: colors.alertSoft,
  },
  otpRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  otpBox: {
    flex: 1,
    height: 56,
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.default,
    textAlign: 'center',
    fontFamily: fontFamilies.mono,
    fontSize: 24,
    color: colors.textPrimary,
  },
  otpBoxFilled: {
    borderColor: colors.forge,
  },
  submitButton: {
    marginBottom: spacing.xl,
  },
  resendRow: {
    alignItems: 'center',
  },
  resendText: {
    ...typeScale.body1,
    color: colors.forge,
  },
  resendCooldownText: {
    ...typeScale.body2,
    color: colors.textTertiary,
  },
});
```

---

## Step 9: Create navigation types and AuthNavigator

**File: `src/navigation/types.ts`**

```typescript
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  VerifyPhone: undefined;
};

export type RenterTabParamList = {
  Search: undefined;
  Bookings: undefined;
  Messages: undefined;
  Profile: undefined;
};

export type OwnerTabParamList = {
  Listings: undefined;
  Bookings: undefined;
  Messages: undefined;
  Profile: undefined;
};

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
};
```

**File: `src/navigation/AuthNavigator.tsx`**

```tsx
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { LoginScreen } from '../screens/auth/LoginScreen';
import { RegisterScreen } from '../screens/auth/RegisterScreen';
import { VerifyPhoneScreen } from '../screens/auth/VerifyPhoneScreen';
import { colors } from '../theme';
import type { AuthStackParamList } from './types';

const Stack = createNativeStackNavigator<AuthStackParamList>();

export function AuthNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.abyss },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="VerifyPhone" component={VerifyPhoneScreen} />
    </Stack.Navigator>
  );
}
```

---

## Step 10: Update the RootNavigator

Replace the placeholder `src/navigation/RootNavigator.tsx` with the version that imports `AuthNavigator` and splits on auth state:

**File: `src/navigation/RootNavigator.tsx`**

```tsx
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuthStore } from '../store/authStore';
import { AuthNavigator } from './AuthNavigator';
import { RenterTabs } from './RenterTabs';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  const needsPhoneVerification =
    isAuthenticated && user && !user.is_phone_verified;

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      ) : (
        <Stack.Screen name="Main" component={RenterTabs} />
      )}
    </Stack.Navigator>
  );
}
```

> **Note:** The `needsPhoneVerification` variable is computed but not gated here intentionally. After registration, the `RegisterScreen` navigates directly to `VerifyPhoneScreen` within the `AuthNavigator`. Once phone verification succeeds, `useAuth.handleVerifyPhone` re-fetches the user profile (which now has `is_phone_verified: true`) and the `RootNavigator` re-renders, swapping to `Main`. If you want to enforce a hard gate where unverified users cannot access `Main`, wrap the `Main` screen with an additional check and redirect to a standalone `VerifyPhoneScreen` outside the `AuthNavigator`.

---

## Step 11: Update the auth store for phone verification flow

Ensure `src/store/authStore.ts` matches the following. The key addition is that `hydrate` now fetches the user profile from the API when a token exists, so the app has the full `User` object (including `is_phone_verified`) on launch:

**File: `src/store/authStore.ts`**

```typescript
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import type { User, AuthTokens } from '../api/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => Promise<void>;
  clearAuth: () => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => set({ user, isAuthenticated: true }),

  setTokens: async (tokens) => {
    await SecureStore.setItemAsync('access_token', tokens.access);
    await SecureStore.setItemAsync('refresh_token', tokens.refresh);
  },

  clearAuth: async () => {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  hydrate: async () => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        set({ isAuthenticated: true, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));
```

---

## Step 12: Test the full auth flow

Start the backend dev server and the Expo app. Test every path below.

### 12a. Test registration

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.mobile@terminal.app",
    "phone": "08123456789",
    "first_name": "Test",
    "last_name": "Mobile",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }' | python3 -m json.tool
```

**Expected:** HTTP 201 with `success: true`, `tokens`, and `user` object. Backend console prints `[DEV OTP]` with a 6-digit code.

### 12b. Test login

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.mobile@terminal.app",
    "password": "TestPass123!"
  }' | python3 -m json.tool
```

**Expected:** HTTP 200 with `access` and `refresh` tokens.

### 12c. Test phone verification

Use the access token from registration and the OTP code from the console:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/verify-phone/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"otp_code": "<OTP_FROM_CONSOLE>"}' | python3 -m json.tool
```

**Expected:** HTTP 200 with `success: true`, `message: "Phone verified successfully."`

### 12d. Test resend OTP

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/resend-otp/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | python3 -m json.tool
```

**Expected:** HTTP 200 with `success: true`. New `[DEV OTP]` printed to console.

### 12e. Test fetch user profile

```bash
curl -s -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | python3 -m json.tool
```

**Expected:** HTTP 200 with `success: true`, `data` containing full user profile with `is_phone_verified: true` after step 12c.

### 12f. Test token refresh

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}' | python3 -m json.tool
```

**Expected:** HTTP 200 with new `access` token.

### 12g. Test logout

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"refresh": "<REFRESH_TOKEN>"}' | python3 -m json.tool
```

**Expected:** HTTP 200 with `success: true`. Subsequent requests with the old refresh token should fail.

### 12h. Test the mobile screens

Open the Expo app (simulator or device):

1. **LoginScreen**: Verify dark background (`#0C0C0F`), input fields on `#1A1A22` background, forge orange focus border, heading in Barlow Condensed 700 uppercase, body in IBM Plex Sans. Submit with empty fields — form validation errors appear. Submit with wrong credentials — error banner appears with actionable message.

2. **RegisterScreen**: Navigate via "Register" link. Fill all fields. Submit with mismatched passwords — validation error on confirm field. Submit with valid data — auto-login, navigate to VerifyPhoneScreen.

3. **VerifyPhoneScreen**: OTP boxes render in mono font. Enter the OTP from console. Each digit auto-advances. Verify succeeds, app navigates to main tabs. Test resend with 60s cooldown.

---

## Step 13: Commit

```bash
git add .
git commit -m "feat(mobile): Wave 01 — Authentication module complete"
```

---

## Definition of Done

Verify every item before proceeding to Wave 02.

**API modules:**
- [ ] `src/api/auth.ts` exports: `register`, `login`, `verifyPhone`, `resendOtp`, `refreshToken`, `logout`
- [ ] `src/api/users.ts` exports: `fetchMe`, `updateProfile`
- [ ] All functions use `apiClient` from `src/api/client.ts` (JWT interceptor attached)
- [ ] Request/response types match the backend API exactly

**Validation:**
- [ ] `src/utils/validation.ts` exports: `loginSchema`, `registerSchema`, `verifyPhoneSchema`
- [ ] Email: valid email format
- [ ] Phone: Nigerian format (`/^0[789]\d{9}$/` — 08/09/07 prefix, 11 digits total)
- [ ] Password: minimum 8 characters
- [ ] `password_confirm` must match `password` (zod `.refine`)
- [ ] All error messages are actionable, no emoji, no exclamation marks

**Screens:**
- [ ] `LoginScreen` renders with `#0C0C0F` background
- [ ] `LoginScreen` heading is "SIGN IN" in `display3` (Barlow Condensed 700, 28px, uppercase)
- [ ] `LoginScreen` has email and password fields with `#1A1A22` background, `#2A2A36` border
- [ ] `LoginScreen` primary CTA text is "Request booking"
- [ ] `LoginScreen` button is forge orange (`#E8750A`), 4px border-radius, 44px height
- [ ] `LoginScreen` has "Register" link to navigate to `RegisterScreen`
- [ ] `RegisterScreen` has fields: email, phone (with +234 prefix), first name, last name, password, confirm password
- [ ] `RegisterScreen` heading is "CREATE ACCOUNT" in `display3`
- [ ] `RegisterScreen` on success: auto-login (tokens stored, user set), navigate to `VerifyPhoneScreen`
- [ ] `VerifyPhoneScreen` renders 6 individual digit input boxes
- [ ] `VerifyPhoneScreen` OTP boxes use mono font (`IBMPlexMono_400Regular`)
- [ ] `VerifyPhoneScreen` digits auto-advance on entry, auto-backspace on delete
- [ ] `VerifyPhoneScreen` supports paste (distributes digits across boxes)
- [ ] `VerifyPhoneScreen` has "Resend code" button with 60s cooldown timer
- [ ] `VerifyPhoneScreen` on verify success: re-fetches user profile, navigates to main app

**Design compliance:**
- [ ] Screen horizontal padding is 20px
- [ ] All spacing values are from the 4px scale: 4 8 12 16 20 24 32 40 48 64 80 96
- [ ] Input border: 1px `#2A2A36`, focus border: `#E8750A`
- [ ] Button primary: `#E8750A`, 4px border-radius, 44px height
- [ ] Text colors: `#F1F1F8` primary, `#8E8EA8` secondary, `#52526A` tertiary
- [ ] Error banner: `#4A1010` background, `#F87171` text
- [ ] No emoji in any user-facing text
- [ ] No exclamation marks in any user-facing text

**Auth store integration:**
- [ ] On login success: tokens stored in SecureStore, user set in Zustand
- [ ] On register success: tokens stored in SecureStore, user set in Zustand
- [ ] On logout: SecureStore cleared, Zustand state reset
- [ ] `hydrate()` checks SecureStore on app launch and restores auth state

**Navigation:**
- [ ] `AuthNavigator` is a native stack: Login → Register → VerifyPhone
- [ ] `RootNavigator` switches between Auth and Main based on `isAuthenticated`
- [ ] Navigation type params defined in `src/navigation/types.ts`
- [ ] After full auth (login or register + verify), user sees the Main tabs

**Hook:**
- [ ] `useAuth` hook exports: `handleLogin`, `handleRegister`, `handleVerifyPhone`, `handleResendOtp`, `handleLogout`, `isLoading`, `error`, `setError`
- [ ] All API errors are caught and set as user-friendly messages
- [ ] Loading state is managed correctly (set true before request, false after)

**Backend integration (test with curl):**
- [ ] `POST /api/v1/auth/register/` returns 201 with tokens and user
- [ ] `POST /api/v1/auth/login/` returns 200 with access and refresh tokens
- [ ] `POST /api/v1/auth/verify-phone/` returns 200 on correct OTP
- [ ] `POST /api/v1/auth/resend-otp/` returns 200 and prints new OTP to console
- [ ] `GET /api/v1/users/me/` returns 200 with full user profile
- [ ] `POST /api/v1/auth/token/refresh/` returns new access token
- [ ] `POST /api/v1/auth/logout/` blacklists refresh token

**General:**
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] No lint errors
- [ ] Git commit made with message `feat(mobile): Wave 01 — Authentication module complete`
