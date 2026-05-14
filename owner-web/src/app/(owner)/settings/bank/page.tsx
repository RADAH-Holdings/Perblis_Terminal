"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/tds/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Field } from "@/components/ui/Field";
import { Skeleton } from "@/components/tds/LoadingSkeleton";
import { ownerSettingsApi } from "@/lib/api/owner";
import { QUERY_KEYS } from "@/lib/constants";

const schema = z.object({
  bank_name: z.string().min(2, "Required."),
  bank_account_number: z
    .string()
    .regex(/^\d{10}$/, "Account number must be exactly 10 digits."),
  bank_account_name: z.string().min(2, "Required."),
});

type FormValues = z.infer<typeof schema>;

export default function BankAccountPage() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: QUERY_KEYS.bankAccount,
    queryFn: () => ownerSettingsApi.getBank().then((r) => r.data),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (q.data) {
      reset({
        bank_name: q.data.bank_name ?? "",
        bank_account_number: q.data.bank_account_number ?? "",
        bank_account_name: q.data.bank_account_name ?? "",
      });
    }
  }, [q.data, reset]);

  const save = useMutation({
    mutationFn: (v: FormValues) => ownerSettingsApi.patchBank(v),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEYS.bankAccount }),
  });

  if (q.isLoading) return <Skeleton className="h-[300px]" />;

  return (
    <>
      <PageHeader
        title="Bank account"
        description="Used for payouts. Must match the business name on file."
      />

      <Card className="max-w-[520px] space-y-4">
        <form onSubmit={handleSubmit((v) => save.mutate(v))} className="space-y-4" noValidate>
          <Field id="bank_name" label="Bank" error={errors.bank_name?.message}>
            <Input id="bank_name" {...register("bank_name")} invalid={!!errors.bank_name} />
          </Field>
          <Field
            id="bank_account_number"
            label="Account number"
            hint="10 digits, no spaces."
            error={errors.bank_account_number?.message}
          >
            <Input
              id="bank_account_number"
              inputMode="numeric"
              maxLength={10}
              className="font-mono"
              invalid={!!errors.bank_account_number}
              {...register("bank_account_number")}
            />
          </Field>
          <Field
            id="bank_account_name"
            label="Account name"
            error={errors.bank_account_name?.message}
          >
            <Input
              id="bank_account_name"
              {...register("bank_account_name")}
              invalid={!!errors.bank_account_name}
            />
          </Field>

          {save.error ? (
            <p className="text-[13px] text-alert-soft">{(save.error as Error).message}</p>
          ) : null}

          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? "Saving\u2026" : "Save"}
          </Button>
        </form>
      </Card>
    </>
  );
}
