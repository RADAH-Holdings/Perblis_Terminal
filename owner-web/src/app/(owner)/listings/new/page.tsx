"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { z } from "zod";

import { PageHeader } from "@/components/layout/PageHeader";
import { ListingSpecsSection } from "@/components/listings/ListingSpecsSection";
import {
  LocationPicker,
  type LocationPickerValue,
} from "@/components/listings/LocationPicker";
import { pickSpecsForApi, specsFormBaseDefaults } from "@/components/listings/listingSpecConfig";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/lib/api/client";
import { listingsApi, type ListingCreatePayload } from "@/lib/api/listings";
import { RESOURCE_TYPES, type ResourceType } from "@/lib/constants";

const optionalNumber = z.preprocess((v) => {
  if (v === "" || v === null || v === undefined) return undefined;
  if (typeof v === "number") return Number.isFinite(v) ? v : undefined;
  if (typeof v === "string") {
    const n = Number(v);
    return Number.isFinite(n) ? n : undefined;
  }
  return undefined;
}, z.number().optional());

const specFormValue = z.union([z.string(), z.number(), z.boolean(), z.undefined()]);
const specsSchema = z.record(z.string(), specFormValue).default({});

const schema = z
  .object({
    resource_type: z.enum(RESOURCE_TYPES),
    title: z.string().min(3, "Required."),
    description: z.string().min(20, "Describe the asset — 20 characters minimum."),
    category: z.string().optional(),
    price_daily: optionalNumber,
    price_weekly: optionalNumber,
    price_monthly: optionalNumber,
    location_address: z.string().optional(),
    location_city: z.string().optional(),
    latitude: optionalNumber.refine(
      (v) => v === undefined || (v >= -90 && v <= 90),
      { message: "Latitude must be between -90 and 90." },
    ),
    longitude: optionalNumber.refine(
      (v) => v === undefined || (v >= -180 && v <= 180),
      { message: "Longitude must be between -180 and 180." },
    ),
    operator_available: z.boolean().optional(),
    delivery_available: z.boolean().optional(),
    specs: specsSchema,
  })
  .superRefine((data, ctx) => {
    if (data.resource_type !== "facility") return;
    const p = data.specs.paved_percent;
    if (p === undefined || p === null || p === "") return;
    const n = typeof p === "number" ? p : Number(String(p).trim());
    if (!Number.isFinite(n) || n < 0 || n > 100) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Enter a percentage between 0 and 100.",
        path: ["specs", "paved_percent"],
      });
    }
  });

type FormInput = z.input<typeof schema>;
type FormValues = z.output<typeof schema>;

const STEPS = [
  { label: "Type" },
  { label: "Details" },
  { label: "Pricing" },
  { label: "Photos" },
  { label: "Location" },
  { label: "Review" },
] as const;

function valuesToPayload(v: FormValues): ListingCreatePayload {
  return {
    resource_type: v.resource_type,
    title: v.title,
    description: v.description,
    category: v.category || undefined,
    price_daily: v.price_daily,
    price_weekly: v.price_weekly,
    price_monthly: v.price_monthly,
    specs: pickSpecsForApi(v.resource_type, v.specs),
    latitude: v.latitude,
    longitude: v.longitude,
    location_address: v.location_address || undefined,
    location_city: v.location_city || undefined,
    operator_available: v.operator_available ?? false,
    delivery_available: v.delivery_available ?? false,
  };
}

export default function NewListingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);

  const {
    register,
    handleSubmit,
    control,
    setValue,
    getValues,
    trigger,
    formState: { errors },
  } = useForm<FormInput, unknown, FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      resource_type: "equipment",
      operator_available: false,
      delivery_available: false,
      specs: specsFormBaseDefaults("equipment"),
    } as FormInput,
  });

  const resourceType = (useWatch({ control, name: "resource_type" }) ??
    "equipment") as ResourceType;
  const prevRt = useRef<ResourceType | null>(null);

  useEffect(() => {
    if (prevRt.current === null) {
      prevRt.current = resourceType;
      return;
    }
    if (prevRt.current !== resourceType) {
      prevRt.current = resourceType;
      setValue("specs", specsFormBaseDefaults(resourceType));
    }
  }, [resourceType, setValue]);

  const create = useMutation({
    mutationFn: (v: FormValues) => listingsApi.create(valuesToPayload(v)),
    onSuccess: (listing) => router.replace(`/listings/${listing.id}/edit`),
  });

  const errorMessage = (() => {
    if (!create.error) return null;
    if (create.error instanceof ApiError) {
      const body = create.error.body as { errors?: Record<string, string[] | string> } | undefined;
      if (body?.errors && typeof body.errors === "object") {
        const first = Object.values(body.errors)[0];
        if (Array.isArray(first) && first[0]) return first[0];
        if (typeof first === "string") return first;
      }
      return create.error.message || "Could not create the listing.";
    }
    return (create.error as Error).message;
  })();

  const fieldsForStep: Record<number, (keyof FormInput)[]> = {
    0: ["resource_type", "category"],
    1: ["title", "description"],
    2: ["price_daily", "price_weekly", "price_monthly"],
    3: [],
    4: ["latitude", "longitude", "location_address", "location_city"],
    5: [],
  };

  async function handleContinue() {
    const fields = fieldsForStep[step] ?? [];
    if (fields.length > 0) {
      const valid = await trigger(fields);
      if (!valid) return;
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function handleBack() {
    setStep((s) => Math.max(s - 1, 0));
  }

  function onFinalSubmit(v: FormValues) {
    create.mutate(v);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="New listing"
        title="Add asset"
        description="Complete each step then save your draft."
      />

      <StepIndicator current={step} />

      <form
        onSubmit={handleSubmit(onFinalSubmit)}
        className="max-w-[720px] space-y-8"
        noValidate
      >
        {step === 0 && (
          <StepTypeCategory register={register} errors={errors} />
        )}

        {step === 1 && (
          <StepDetails
            register={register}
            errors={errors}
            resourceType={resourceType}
          />
        )}

        {step === 2 && <StepPricing register={register} />}

        {step === 3 && <StepPhotos />}

        {step === 4 && (
          <StepLocation
            getValues={getValues}
            setValue={setValue}
          />
        )}

        {step === 5 && (
          <StepReview
            getValues={getValues}
            submitting={create.isPending}
          />
        )}

        <div className="flex items-center gap-3 pt-2">
          {step > 0 && (
            <Button type="button" variant="secondary" size="md" onClick={handleBack}>
              Back
            </Button>
          )}
          {step < STEPS.length - 1 && (
            <Button type="button" size="md" onClick={handleContinue}>
              Continue
            </Button>
          )}
          {step === STEPS.length - 1 && (
            <Button type="submit" size="lg" disabled={create.isPending}>
              {create.isPending ? "Saving…" : "Save Draft"}
            </Button>
          )}
        </div>

        {errorMessage && (
          <p className="text-alert-soft text-[13px]">{errorMessage}</p>
        )}
      </form>
    </div>
  );
}

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2">
      {STEPS.map((s, i) => {
        const isActive = i === current;
        const isCompleted = i < current;
        return (
          <div key={i} className="flex items-center gap-1">
            {i > 0 && (
              <div
                className={`mx-1 h-px w-4 sm:w-6 ${
                  isCompleted ? "bg-forge" : "bg-border"
                }`}
              />
            )}
            <div className="flex flex-col items-center gap-1">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-[12px] font-medium ${
                  isActive
                    ? "bg-forge text-text-on-accent"
                    : isCompleted
                      ? "bg-forge/20 text-forge"
                      : "bg-surface-elevated text-text-tertiary border border-border"
                }`}
              >
                {i + 1}
              </div>
              <span
                className={`text-[10px] sm:text-[11px] ${
                  isActive
                    ? "text-forge font-medium"
                    : isCompleted
                      ? "text-text-secondary"
                      : "text-text-tertiary"
                }`}
              >
                {s.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StepTypeCategory({
  register,
  errors,
}: {
  register: ReturnType<typeof useForm<FormInput>>["register"];
  errors: ReturnType<typeof useForm<FormInput>>["formState"]["errors"];
}) {
  return (
    <section className="space-y-4">
      <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">
        Asset type &amp; category
      </h2>
      <Field id="resource_type" label="Resource type" error={errors.resource_type?.message}>
        <select
          id="resource_type"
          className="border-border bg-surface-elevated h-10 w-full rounded border px-3 text-[14px]"
          {...register("resource_type")}
        >
          {RESOURCE_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </Field>
      <Field id="category" label="Category" hint="Free text e.g. mobile crane, flatbed 30t.">
        <Input id="category" {...register("category")} />
      </Field>
    </section>
  );
}

function StepDetails({
  register,
  errors,
  resourceType,
}: {
  register: ReturnType<typeof useForm<FormInput>>["register"];
  errors: ReturnType<typeof useForm<FormInput>>["formState"]["errors"];
  resourceType: ResourceType;
}) {
  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">
          Details
        </h2>
        <Field id="title" label="Title" error={errors.title?.message}>
          <Input id="title" invalid={!!errors.title} {...register("title")} />
        </Field>
        <Field id="description" label="Description" error={errors.description?.message}>
          <textarea
            id="description"
            rows={6}
            className="border-border bg-surface-elevated font-body text-text-primary placeholder:text-text-tertiary focus:border-border-active w-full rounded border p-3 text-[14px] focus:outline-none"
            {...register("description")}
          />
        </Field>
      </section>

      <ListingSpecsSection resourceType={resourceType} register={register} errors={errors} />

      <section className="space-y-3">
        <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">Options</h2>
        <label className="flex items-center gap-3 text-[14px]">
          <input type="checkbox" {...register("operator_available")} />
          Operator can be provided
        </label>
        <label className="flex items-center gap-3 text-[14px]">
          <input type="checkbox" {...register("delivery_available")} />
          Delivery available
        </label>
      </section>
    </div>
  );
}

function StepPricing({
  register,
}: {
  register: ReturnType<typeof useForm<FormInput>>["register"];
}) {
  return (
    <section className="space-y-4">
      <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">Pricing</h2>
      <p className="text-text-tertiary text-[12px]">
        Set at least one price tier. Prices are in Nigerian Naira (₦).
      </p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Field id="price_daily" label="Daily (₦)">
          <Input
            id="price_daily"
            inputMode="numeric"
            className="font-mono"
            {...register("price_daily")}
          />
        </Field>
        <Field id="price_weekly" label="Weekly (₦)">
          <Input
            id="price_weekly"
            inputMode="numeric"
            className="font-mono"
            {...register("price_weekly")}
          />
        </Field>
        <Field id="price_monthly" label="Monthly (₦)">
          <Input
            id="price_monthly"
            inputMode="numeric"
            className="font-mono"
            {...register("price_monthly")}
          />
        </Field>
      </div>
    </section>
  );
}

function StepPhotos() {
  return (
    <section className="space-y-4">
      <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">Photos</h2>
      <div className="border-border bg-surface rounded-lg border border-dashed p-8 text-center">
        <p className="text-text-secondary text-[14px]">
          Photos are uploaded after creating the listing.
        </p>
        <p className="text-text-tertiary mt-2 text-[12px]">
          After saving your draft, you&apos;ll be redirected to the edit page where you can upload
          and manage photos.
        </p>
      </div>
    </section>
  );
}

function StepLocation({
  getValues,
  setValue,
}: {
  getValues: ReturnType<typeof useForm<FormInput>>["getValues"];
  setValue: ReturnType<typeof useForm<FormInput>>["setValue"];
}) {
  const values = getValues();
  const lat = values.latitude;
  const lng = values.longitude;
  const addr = (values.location_address as string) || "";
  const cty = (values.location_city as string) || "";

  const parsedLat =
    lat === undefined || lat === "" ? undefined : Number(lat);
  const parsedLng =
    lng === undefined || lng === "" ? undefined : Number(lng);

  function handleChange(loc: LocationPickerValue) {
    setValue("latitude", loc.latitude as unknown as string, { shouldValidate: false });
    setValue("longitude", loc.longitude as unknown as string, { shouldValidate: false });
    setValue("location_address", loc.address, { shouldValidate: false });
    setValue("location_city", loc.city, { shouldValidate: false });
  }

  return (
    <section className="space-y-4">
      <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">Location</h2>
      <LocationPicker
        latitude={Number.isFinite(parsedLat) ? parsedLat : undefined}
        longitude={Number.isFinite(parsedLng) ? parsedLng : undefined}
        address={addr}
        city={cty}
        onChange={handleChange}
      />
    </section>
  );
}

function StepReview({
  getValues,
  submitting,
}: {
  getValues: ReturnType<typeof useForm<FormInput>>["getValues"];
  submitting: boolean;
}) {
  const v = getValues();

  const rows: { label: string; value: string }[] = [
    { label: "Resource type", value: v.resource_type || "—" },
    { label: "Category", value: (v.category as string) || "—" },
    { label: "Title", value: (v.title as string) || "—" },
    {
      label: "Description",
      value: (v.description as string)?.slice(0, 120) + ((v.description as string)?.length > 120 ? "…" : "") || "—",
    },
    { label: "Daily price", value: v.price_daily ? `₦${v.price_daily}` : "—" },
    { label: "Weekly price", value: v.price_weekly ? `₦${v.price_weekly}` : "—" },
    { label: "Monthly price", value: v.price_monthly ? `₦${v.price_monthly}` : "—" },
    { label: "Address", value: (v.location_address as string) || "—" },
    { label: "City", value: (v.location_city as string) || "—" },
    {
      label: "Coordinates",
      value:
        v.latitude && v.longitude
          ? `${v.latitude}, ${v.longitude}`
          : "—",
    },
    { label: "Operator available", value: v.operator_available ? "Yes" : "No" },
    { label: "Delivery available", value: v.delivery_available ? "Yes" : "No" },
  ];

  return (
    <section className="space-y-4">
      <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase">
        Review &amp; Publish
      </h2>
      <p className="text-text-tertiary text-[12px]">
        Confirm the details below, then save as a draft. You can edit everything later.
      </p>
      <div className="border-border bg-surface divide-border divide-y rounded border">
        {rows.map((r) => (
          <div key={r.label} className="flex items-start justify-between gap-4 px-4 py-3">
            <span className="text-text-secondary text-[13px]">{r.label}</span>
            <span className="text-text-primary text-right text-[13px] font-medium">
              {r.value}
            </span>
          </div>
        ))}
      </div>
      {submitting && (
        <p className="text-text-tertiary text-[12px]">Creating listing…</p>
      )}
    </section>
  );
}
