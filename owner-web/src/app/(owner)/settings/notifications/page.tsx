"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Switch from "@radix-ui/react-switch";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/tds/Card";
import { Skeleton } from "@/components/tds/LoadingSkeleton";
import { ownerSettingsApi } from "@/lib/api/owner";
import { QUERY_KEYS } from "@/lib/constants";

type NotifKey =
  | "notify_new_booking_request"
  | "notify_booking_confirmed"
  | "notify_new_message"
  | "notify_booking_cancelled";

const ROWS: { key: NotifKey; label: string; hint: string }[] = [
  {
    key: "notify_new_booking_request",
    label: "New booking request",
    hint: "A renter wants to book.",
  },
  {
    key: "notify_booking_confirmed",
    label: "Booking confirmed",
    hint: "A renter accepts a counter or pays.",
  },
  { key: "notify_new_message", label: "New message", hint: "Someone replies in a thread." },
  {
    key: "notify_booking_cancelled",
    label: "Booking cancelled",
    hint: "Either side cancels.",
  },
];

type NotifData = Record<NotifKey, boolean>;

export default function NotificationsPage() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: QUERY_KEYS.notifications,
    queryFn: () => ownerSettingsApi.getNotifications().then((r) => r.data),
  });

  const toggle = useMutation({
    mutationFn: (body: Partial<NotifData>) => ownerSettingsApi.patchNotifications(body),
    onMutate: async (partial) => {
      await qc.cancelQueries({ queryKey: QUERY_KEYS.notifications });
      const prev = qc.getQueryData<NotifData>(QUERY_KEYS.notifications);
      qc.setQueryData<NotifData>(QUERY_KEYS.notifications, (old) => ({
        ...(old as NotifData),
        ...partial,
      }));
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(QUERY_KEYS.notifications, ctx.prev);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: QUERY_KEYS.notifications }),
  });

  if (q.isLoading) return <Skeleton className="h-[300px]" />;

  return (
    <>
      <PageHeader title="Notifications" description="Choose what you want to be told about." />
      <Card className="max-w-[640px] divide-y divide-border p-0">
        {ROWS.map((r) => {
          const checked = !!(q.data as NotifData | undefined)?.[r.key];
          return (
            <div key={r.key} className="flex items-center justify-between p-4">
              <div>
                <div className="text-[14px] font-medium">{r.label}</div>
                <div className="text-[12px] text-text-tertiary">{r.hint}</div>
              </div>
              <Switch.Root
                checked={checked}
                onCheckedChange={(v) => toggle.mutate({ [r.key]: v })}
                className="w-10 h-6 rounded-pill bg-surface-high border border-border data-[state=checked]:bg-forge relative"
              >
                <Switch.Thumb className="block w-4 h-4 bg-text-primary rounded-pill translate-x-1 data-[state=checked]:translate-x-5 transition-transform duration-fast" />
              </Switch.Root>
            </div>
          );
        })}
      </Card>
    </>
  );
}
