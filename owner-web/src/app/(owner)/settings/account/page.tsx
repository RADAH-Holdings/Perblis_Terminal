"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/tds/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Field } from "@/components/ui/Field";
import { Badge } from "@/components/tds/Badge";
import { useMe } from "@/hooks/useAuth";
import { authApi } from "@/lib/api/auth";
import { usersApi } from "@/lib/api/users";

export default function AccountSettingsPage() {
  const me = useMe();
  const user = me.data;

  const [oldPwd, setOldPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");

  const changePwd = useMutation({
    mutationFn: () => authApi.changePassword(oldPwd, newPwd, confirmPwd),
    onSuccess: () => {
      setOldPwd("");
      setNewPwd("");
      setConfirmPwd("");
    },
  });

  const upload = useMutation({
    mutationFn: ({ file, type }: { file: File; type: "government_id" | "business_registration" }) =>
      usersApi.uploadDocument(file, type),
    onSuccess: () => me.refetch(),
  });

  const role = useMutation({
    mutationFn: (renter: boolean) => usersApi.updateRole(true, renter),
    onSuccess: () => me.refetch(),
  });

  return (
    <>
      <PageHeader title="Account" description="Identity, role, and password." />

      <div className="space-y-6 max-w-[680px]">
        <Card className="space-y-3">
          <div className="text-[11px] uppercase tracking-[0.06em] text-text-tertiary">
            Identity
          </div>
          <div className="grid grid-cols-2 gap-3 font-mono text-[13px]">
            <div>
              <div className="text-text-tertiary text-[11px] uppercase tracking-[0.06em]">
                Email
              </div>
              <div className="mt-1">{user?.email}</div>
            </div>
            <div>
              <div className="text-text-tertiary text-[11px] uppercase tracking-[0.06em]">
                Phone
              </div>
              <div className="mt-1">{user?.phone}</div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            <Badge tone={user?.is_phone_verified ? "success" : "warn"}>
              {user?.is_phone_verified ? "Phone verified" : "Phone unverified"}
            </Badge>
            <Badge tone={user?.is_email_verified ? "success" : "warn"}>
              {user?.is_email_verified ? "Email verified" : "Email unverified"}
            </Badge>
            <Badge tone={user?.is_id_verified ? "success" : "neutral"}>
              {user?.is_id_verified ? "ID verified" : "ID not submitted"}
            </Badge>
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="text-[11px] uppercase tracking-[0.06em] text-text-tertiary">Role</div>
          <p className="text-[14px] text-text-secondary">
            You are signed in as an owner. Enable renter mode to also book equipment.
          </p>
          <label className="flex items-center gap-3 text-[14px]">
            <input
              type="checkbox"
              checked={user?.is_renter ?? false}
              onChange={(e) => role.mutate(e.target.checked)}
            />
            Also act as a renter
          </label>
        </Card>

        <Card className="space-y-3">
          <div className="text-[11px] uppercase tracking-[0.06em] text-text-tertiary">
            Verification
          </div>
          <p className="text-[14px] text-text-secondary">
            Upload one government ID and one business registration to unlock the verified badge on
            your listings.
          </p>
          <div className="flex flex-wrap gap-2">
            <label className="inline-block">
              <input
                type="file"
                accept="image/*,application/pdf"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) upload.mutate({ file: f, type: "government_id" });
                }}
              />
              <Button asChild variant="secondary" size="sm">
                <span>Upload government ID</span>
              </Button>
            </label>
            <label className="inline-block">
              <input
                type="file"
                accept="image/*,application/pdf"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) upload.mutate({ file: f, type: "business_registration" });
                }}
              />
              <Button asChild variant="secondary" size="sm">
                <span>Upload business registration</span>
              </Button>
            </label>
          </div>
          {upload.isSuccess ? (
            <p className="text-[12px] text-clear-soft font-mono">
              Uploaded. We will review and update your verification status.
            </p>
          ) : null}
        </Card>

        <Card className="space-y-4">
          <div className="text-[11px] uppercase tracking-[0.06em] text-text-tertiary">
            Password
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              changePwd.mutate();
            }}
            className="space-y-3"
          >
            <Field id="old_pwd" label="Current password">
              <Input
                id="old_pwd"
                type="password"
                value={oldPwd}
                onChange={(e) => setOldPwd(e.target.value)}
              />
            </Field>
            <Field id="new_pwd" label="New password">
              <Input
                id="new_pwd"
                type="password"
                value={newPwd}
                onChange={(e) => setNewPwd(e.target.value)}
              />
            </Field>
            <Field id="confirm_pwd" label="Confirm new password">
              <Input
                id="confirm_pwd"
                type="password"
                value={confirmPwd}
                onChange={(e) => setConfirmPwd(e.target.value)}
              />
            </Field>
            {changePwd.error ? (
              <p className="text-[13px] text-alert-soft">
                {(changePwd.error as Error).message}
              </p>
            ) : null}
            {changePwd.isSuccess ? (
              <p className="text-[13px] text-clear-soft">Password changed.</p>
            ) : null}
            <Button
              type="submit"
              disabled={
                changePwd.isPending || !oldPwd || newPwd.length < 8 || newPwd !== confirmPwd
              }
            >
              {changePwd.isPending ? "Updating\u2026" : "Update password"}
            </Button>
          </form>
        </Card>
      </div>
    </>
  );
}
