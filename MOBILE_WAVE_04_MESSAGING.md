# TERMINAL MOBILE — WAVE 04: MESSAGING
> Agent task file. Execute every instruction in order. Do not skip steps.
> Wave 03 must be complete before starting this wave.

---

## Context

This wave implements the in-app messaging system with real-time delivery via Ably. After this wave, renters and owners can chat within booking and inquiry contexts, with messages delivered in real-time.

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/threads/` | List user's threads |
| `POST` | `/api/v1/threads/` | Create inquiry thread |
| `GET` | `/api/v1/threads/{id}/` | Thread detail + messages |
| `POST` | `/api/v1/threads/{id}/messages/` | Send a message |
| `POST` | `/api/v1/threads/token/` | Get Ably auth token |

---

## Step 1: API functions

**File: `src/api/messaging.ts`**

```typescript
import { apiClient } from './client';

export const messagingApi = {
  listThreads: () =>
    apiClient.get('/threads/'),

  createInquiryThread: (data: { listing_id: string; initial_message: string }) =>
    apiClient.post('/threads/', data),

  getThread: (id: string) =>
    apiClient.get(`/threads/${id}/`),

  sendMessage: (threadId: string, body: string) =>
    apiClient.post(`/threads/${threadId}/messages/`, { body }),

  getAblyToken: () =>
    apiClient.post('/threads/token/'),
};
```

---

## Step 2: Ably realtime hook

**File: `src/hooks/useAbly.ts`**

```typescript
import { useEffect, useRef, useCallback } from 'react';
import { AblyRealtime } from 'ably';
import { messagingApi } from '../api/messaging';

export function useAblyChannel(
  threadId: string | null,
  onMessage: (message: any) => void
) {
  const clientRef = useRef<AblyRealtime | null>(null);

  useEffect(() => {
    if (!threadId) return;

    let channel: any;

    const connect = async () => {
      try {
        const { data } = await messagingApi.getAblyToken();
        if (!data.success || !data.token?.token) return;

        const client = new AblyRealtime({ token: data.token.token });
        clientRef.current = client;

        channel = client.channels.get(`thread:${threadId}`);
        channel.subscribe('new_message', (msg: any) => {
          onMessage(msg.data);
        });
      } catch (err) {
        console.log('[Ably] Connection failed, using polling fallback');
      }
    };

    connect();

    return () => {
      channel?.unsubscribe();
      clientRef.current?.close();
    };
  }, [threadId]);
}
```

---

## Step 3: Messaging store

**File: `src/stores/messaging.store.ts`**

```typescript
import { create } from 'zustand';
import { Thread, Message } from '../types/messaging';
import { messagingApi } from '../api/messaging';

interface MessagingState {
  threads: Thread[];
  currentMessages: Message[];
  isLoading: boolean;
  fetchThreads: () => Promise<void>;
  fetchMessages: (threadId: string) => Promise<void>;
  addMessage: (message: Message) => void;
}

export const useMessagingStore = create<MessagingState>((set, get) => ({
  threads: [],
  currentMessages: [],
  isLoading: false,

  fetchThreads: async () => {
    set({ isLoading: true });
    try {
      const { data } = await messagingApi.listThreads();
      set({ threads: data.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchMessages: async (threadId: string) => {
    set({ isLoading: true });
    try {
      const { data } = await messagingApi.getThread(threadId);
      set({ currentMessages: data.messages, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  addMessage: (message: Message) => {
    set((state) => ({
      currentMessages: [...state.currentMessages, message],
    }));
  },
}));
```

---

## Step 4: Screens

### Messages Tab Screen (`app/(tabs)/messages.tsx`)

**UI requirements:**
- List of conversation threads
- Each thread card shows:
  - Other participant's avatar + name
  - Listing title (context)
  - Last message preview (truncated to 1 line)
  - Timestamp (relative: "2m ago", "1h ago", "3d ago")
  - Unread count badge (if > 0)
  - Thread type indicator: 🔖 booking thread vs 💬 inquiry thread
- Pull to refresh
- Empty state: "No conversations yet"
- Tapping a thread → navigate to `thread/[id]`

**Flow:**
1. Fetch `GET /api/v1/threads/`
2. Render sorted by `updated_at` (most recent first)
3. Unread badge shows `unread_count` from API

### Chat Screen (`app/thread/[id].tsx`)

**UI requirements:**
- Header: other participant name + avatar, listing title subtitle
- Message list (FlatList, inverted for chat UX):
  - Own messages: right-aligned, primary color background
  - Other's messages: left-aligned, gray background
  - Each bubble shows: body text, timestamp below
  - Date separators between days
- Chat input at bottom:
  - Text input (multiline, max 3 lines)
  - Send button (icon, disabled when empty)
- Auto-scroll to bottom on new message
- KeyboardAvoidingView for proper input positioning
- "Typing..." indicator (optional, use Ably presence)

**Flow:**
1. Fetch `GET /api/v1/threads/{id}/` → thread info + all messages
2. Subscribe to Ably channel `thread:{id}` for real-time messages
3. When user sends:
   a. Optimistically add message to UI
   b. `POST /api/v1/threads/{id}/messages/`
   c. If fails → mark message as failed, show retry option
4. When Ably delivers a new message from other party:
   a. Add to message list
   b. Auto-scroll to bottom
5. On screen enter → messages from other party are marked as read (server does this)

### Send Inquiry (from Listing Detail)

**Triggered from**: "Send Inquiry" button on listing detail

**UI:**
- Modal/bottom sheet with:
  - Text area: "Write your message to {owner_name}..."
  - "Send" button
- Submit → `POST /api/v1/threads/` with `{ listing_id, initial_message }`
- On success → navigate directly to the new thread's chat screen

---

## Step 5: Components

### Thread Card (`src/components/messaging/ThreadCard.tsx`)

Props:
- `thread: Thread`
- `onPress: () => void`

Renders: avatar, name, last message preview, time, unread badge.

### Message Bubble (`src/components/messaging/MessageBubble.tsx`)

Props:
- `message: Message`
- `isOwn: boolean`

Renders: colored bubble, text, timestamp.

### Chat Input (`src/components/messaging/ChatInput.tsx`)

Props:
- `onSend: (text: string) => void`
- `disabled?: boolean`

Renders: text input + send button.

---

## Step 6: Unread badge on tab icon

The Messages tab icon in the bottom navigation should show a badge with the total unread count. Fetch from `GET /api/v1/users/me/` → `unread_messages` field.

Poll this every 30 seconds while the app is foregrounded, OR update it when Ably delivers a message on any subscribed channel.

---

## Definition of Done

- [ ] Threads list screen shows all conversations sorted by recency
- [ ] Thread cards display: avatar, name, last message, time, unread badge
- [ ] Chat screen renders messages in bubble format (own vs other)
- [ ] Send message works: input → API → optimistic UI update
- [ ] Ably realtime: new messages appear without manual refresh
- [ ] "Send Inquiry" from listing detail creates thread and opens chat
- [ ] "Go to Chat" from booking detail navigates to the correct thread
- [ ] Unread badge on Messages tab icon
- [ ] Auto-scroll to latest message
- [ ] KeyboardAvoidingView keeps input above keyboard
- [ ] Date separators between different days
- [ ] Empty state for no threads
- [ ] Pull to refresh on threads list
- [ ] Graceful fallback if Ably is unavailable (manual refresh button)
- [ ] Git commit: `feat(messaging): Wave 04 — Messaging complete`
