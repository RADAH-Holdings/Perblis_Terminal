"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";

export type LocationPickerValue = {
  latitude: number | undefined;
  longitude: number | undefined;
  address: string;
  city: string;
};

export function LocationPicker({
  latitude,
  longitude,
  address,
  city,
  onChange,
}: {
  latitude: number | undefined;
  longitude: number | undefined;
  address: string;
  city: string;
  onChange: (value: LocationPickerValue) => void;
}) {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  const hasToken = Boolean(token);

  if (!hasToken) {
    return (
      <FallbackInputs
        latitude={latitude}
        longitude={longitude}
        address={address}
        city={city}
        onChange={onChange}
      />
    );
  }

  return (
    <MapPickerWithToken
      token={token!}
      latitude={latitude}
      longitude={longitude}
      address={address}
      city={city}
      onChange={onChange}
    />
  );
}

function FallbackInputs({
  latitude,
  longitude,
  address,
  city,
  onChange,
}: {
  latitude: number | undefined;
  longitude: number | undefined;
  address: string;
  city: string;
  onChange: (value: LocationPickerValue) => void;
}) {
  return (
    <div className="space-y-4">
      <p className="text-text-tertiary text-[12px]">
        No Mapbox token configured. Enter coordinates manually.
      </p>
      <Field id="loc-address" label="Address">
        <Input
          id="loc-address"
          value={address}
          onChange={(e) => onChange({ latitude, longitude, address: e.target.value, city })}
        />
      </Field>
      <Field id="loc-city" label="City">
        <Input
          id="loc-city"
          value={city}
          onChange={(e) => onChange({ latitude, longitude, address, city: e.target.value })}
        />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field id="loc-lat" label="Latitude">
          <Input
            id="loc-lat"
            inputMode="decimal"
            className="font-mono"
            value={latitude ?? ""}
            onChange={(e) => {
              const v = e.target.value;
              const n = v === "" ? undefined : Number(v);
              onChange({
                latitude: n !== undefined && Number.isFinite(n) ? n : undefined,
                longitude,
                address,
                city,
              });
            }}
          />
        </Field>
        <Field id="loc-lng" label="Longitude">
          <Input
            id="loc-lng"
            inputMode="decimal"
            className="font-mono"
            value={longitude ?? ""}
            onChange={(e) => {
              const v = e.target.value;
              const n = v === "" ? undefined : Number(v);
              onChange({
                latitude,
                longitude: n !== undefined && Number.isFinite(n) ? n : undefined,
                address,
                city,
              });
            }}
          />
        </Field>
      </div>
    </div>
  );
}

function MapPickerWithToken({
  token,
  latitude,
  longitude,
  address,
  city,
  onChange,
}: {
  token: string;
  latitude: number | undefined;
  longitude: number | undefined;
  address: string;
  city: string;
  onChange: (value: LocationPickerValue) => void;
}) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const [mapReady, setMapReady] = useState(false);

  const onChangeRef = useRef(onChange);
  const latRef = useRef(latitude);
  const lngRef = useRef(longitude);
  const addressRef = useRef(address);
  const cityRef = useRef(city);

  useEffect(() => {
    onChangeRef.current = onChange;
    latRef.current = latitude;
    lngRef.current = longitude;
    addressRef.current = address;
    cityRef.current = city;
  });

  useEffect(() => {
    if (!mapContainerRef.current) return;

    let cancelled = false;

    async function initMap() {
      const mapboxgl = (await import("mapbox-gl")).default;
      await import("mapbox-gl/dist/mapbox-gl.css");

      if (cancelled || !mapContainerRef.current) return;

      mapboxgl.accessToken = token;

      const initialLng = lngRef.current ?? 3.39;
      const initialLat = latRef.current ?? 6.45;

      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/dark-v11",
        center: [initialLng, initialLat],
        zoom: latRef.current !== undefined ? 13 : 10,
      });

      mapRef.current = map;

      if (latRef.current !== undefined && lngRef.current !== undefined) {
        const marker = new mapboxgl.Marker({ color: "#E8750A" })
          .setLngLat([lngRef.current, latRef.current])
          .addTo(map);
        markerRef.current = marker;
      }

      map.on("click", (e) => {
        const { lng, lat } = e.lngLat;

        if (markerRef.current) {
          markerRef.current.setLngLat([lng, lat]);
        } else {
          const marker = new mapboxgl.Marker({ color: "#E8750A" })
            .setLngLat([lng, lat])
            .addTo(map);
          markerRef.current = marker;
        }

        onChangeRef.current({
          latitude: Math.round(lat * 1_000_000) / 1_000_000,
          longitude: Math.round(lng * 1_000_000) / 1_000_000,
          address: addressRef.current,
          city: cityRef.current,
        });
      });

      map.on("load", () => {
        if (!cancelled) setMapReady(true);
      });
    }

    initMap();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      markerRef.current = null;
    };
  }, [token]);

  const handleAddressChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({ latitude, longitude, address: e.target.value, city });
    },
    [latitude, longitude, city, onChange],
  );

  const handleCityChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({ latitude, longitude, address, city: e.target.value });
    },
    [latitude, longitude, address, onChange],
  );

  return (
    <div className="space-y-4">
      <p className="text-text-tertiary text-[12px]">
        Click on the map to set the asset location.
      </p>
      <div className="border-border relative h-[300px] w-full overflow-hidden rounded border">
        <div ref={mapContainerRef} className="h-full w-full" />
        {!mapReady && (
          <div className="bg-surface absolute inset-0 flex items-center justify-center">
            <span className="text-text-tertiary text-[13px]">Loading map…</span>
          </div>
        )}
      </div>
      {latitude !== undefined && longitude !== undefined && (
        <p className="font-mono text-text-secondary text-[12px]">
          {latitude.toFixed(6)}, {longitude.toFixed(6)}
        </p>
      )}
      <Field id="loc-address" label="Address">
        <Input id="loc-address" value={address} onChange={handleAddressChange} />
      </Field>
      <Field id="loc-city" label="City">
        <Input id="loc-city" value={city} onChange={handleCityChange} />
      </Field>
    </div>
  );
}
