"use client";

import { useMemo, useState } from "react";
import { Map, Source, Layer, Popup, NavigationControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { MapLayerMouseEvent } from "react-map-gl/maplibre";
import type { FeatureCollection, Point } from "geojson";
import {
  POLLUTANT_BY_CODE,
  STATUS_BY_CODE,
} from "@/lib/constants";
import type { StationLatestRow } from "@/lib/queries";

const SEOUL_CENTER = { longitude: 126.98, latitude: 37.56 };
const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

type Popped = {
  row: StationLatestRow;
  longitude: number;
  latitude: number;
} | null;

export function StationMap({
  rows,
  pollutantCode,
}: {
  rows: StationLatestRow[];
  pollutantCode: number;
}) {
  const pollutant = POLLUTANT_BY_CODE[pollutantCode];
  const threshold = pollutant?.threshold ?? 0;
  const [popped, setPopped] = useState<Popped>(null);

  const geojson = useMemo<FeatureCollection<Point>>(() => {
    const max = Math.max(
      1e-9,
      ...rows.map((r) => (r.value ?? 0) as number)
    );
    return {
      type: "FeatureCollection",
      features: rows
        .filter(
          (r): r is StationLatestRow & { value: number } =>
            r.latitude != null && r.longitude != null && r.value != null
        )
        .map((r) => ({
          type: "Feature",
          properties: {
            station_code: r.station_code,
            value: r.value,
            record_count: r.record_count,
            dominant_status: r.dominant_status,
            above: r.value > threshold ? 1 : 0,
            normalized: r.value / max,
          },
          geometry: {
            type: "Point",
            coordinates: [Number(r.longitude), Number(r.latitude)],
          },
        })),
    };
  }, [rows, threshold]);

  const handleClick = (e: MapLayerMouseEvent) => {
    const f = e.features?.[0];
    if (!f) {
      setPopped(null);
      return;
    }
    const geom = f.geometry as Point;
    const props = f.properties as unknown as StationLatestRow & {
      dominant_status: number;
    };
    setPopped({
      row: props,
      longitude: geom.coordinates[0],
      latitude: geom.coordinates[1],
    });
  };

  return (
    <div className="relative h-[520px] w-full overflow-hidden">
      <Map
        initialViewState={{ ...SEOUL_CENTER, zoom: 10.2 }}
        mapStyle={MAP_STYLE}
        interactiveLayerIds={["stations"]}
        onClick={handleClick}
      >
        <NavigationControl position="top-right" showCompass={false} />

        <Source id="stations" type="geojson" data={geojson}>
          <Layer
            id="stations-halo"
            type="circle"
            paint={{
              "circle-radius": [
                "interpolate",
                ["linear"],
                ["get", "normalized"],
                0,
                6,
                1,
                28,
              ],
              "circle-color": [
                "case",
                ["==", ["get", "above"], 1],
                "#ef4444",
                "#22d3ee",
              ],
              "circle-opacity": 0.12,
              "circle-stroke-width": 0,
            }}
          />
          <Layer
            id="stations"
            type="circle"
            paint={{
              "circle-radius": 5,
              "circle-color": [
                "case",
                ["==", ["get", "above"], 1],
                "#ef4444",
                "#22d3ee",
              ],
              "circle-stroke-color": "#0a0a0a",
              "circle-stroke-width": 1.5,
            }}
          />
        </Source>

        {popped && (
          <Popup
            longitude={popped.longitude}
            latitude={popped.latitude}
            closeButton={false}
            closeOnClick
            onClose={() => setPopped(null)}
            offset={10}
            className="font-sans"
          >
            <div className="min-w-[180px] space-y-1.5 text-[0.75rem]">
              <div className="label-eyebrow">Station</div>
              <div className="num text-[0.95rem] font-medium">
                {popped.row.station_code}
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-[var(--color-fg-muted)]">
                <div>
                  <div className="label-eyebrow">Mean</div>
                  <div className="num text-[0.85rem] text-[var(--color-fg)]">
                    {popped.row.value?.toFixed(4)}
                  </div>
                </div>
                <div>
                  <div className="label-eyebrow">Records</div>
                  <div className="num text-[0.85rem] text-[var(--color-fg)]">
                    {popped.row.record_count?.toLocaleString()}
                  </div>
                </div>
              </div>
              <div>
                <div className="label-eyebrow">Status</div>
                <div className="text-[0.8rem] text-[var(--color-fg)]">
                  {STATUS_BY_CODE[popped.row.dominant_status]?.label ??
                    `code ${popped.row.dominant_status}`}
                </div>
              </div>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
