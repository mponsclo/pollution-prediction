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

type PoppedProperties = {
  station_code: number;
  value: number | null;
  record_count: number;
  dominant_status: number | null;
  above: number;
  has_data: number;
};

type Popped = {
  props: PoppedProperties;
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
      ...rows.map((r) => (r.value ?? 0) as number),
    );
    return {
      type: "FeatureCollection",
      features: rows
        .filter((r) => r.latitude != null && r.longitude != null)
        .map((r) => {
          const hasData = r.value != null && r.record_count > 0;
          const above = hasData && (r.value ?? 0) > threshold ? 1 : 0;
          return {
            type: "Feature" as const,
            properties: {
              station_code: r.station_code,
              value: r.value,
              record_count: r.record_count,
              dominant_status: r.dominant_status,
              above,
              has_data: hasData ? 1 : 0,
              normalized: hasData ? (r.value ?? 0) / max : 0,
            },
            geometry: {
              type: "Point" as const,
              coordinates: [Number(r.longitude), Number(r.latitude)],
            },
          };
        }),
    };
  }, [rows, threshold]);

  const stats = useMemo(() => {
    let above = 0;
    let below = 0;
    let missing = 0;
    for (const r of rows) {
      const hasData = r.value != null && r.record_count > 0;
      if (!hasData) missing += 1;
      else if ((r.value ?? 0) > threshold) above += 1;
      else below += 1;
    }
    return { above, below, missing };
  }, [rows, threshold]);

  const handleClick = (e: MapLayerMouseEvent) => {
    const f = e.features?.[0];
    if (!f) {
      setPopped(null);
      return;
    }
    const geom = f.geometry as Point;
    const props = f.properties as unknown as PoppedProperties;
    setPopped({
      props,
      longitude: geom.coordinates[0],
      latitude: geom.coordinates[1],
    });
  };

  return (
    <div className="relative h-[560px] w-full overflow-hidden">
      <Map
        initialViewState={{ ...SEOUL_CENTER, zoom: 10.2 }}
        mapStyle={MAP_STYLE}
        interactiveLayerIds={["stations", "stations-nodata"]}
        onClick={handleClick}
      >
        <NavigationControl position="top-right" showCompass={false} />

        <Source id="stations" type="geojson" data={geojson}>
          <Layer
            id="stations-halo"
            type="circle"
            filter={["==", ["get", "has_data"], 1]}
            paint={{
              "circle-radius": [
                "interpolate",
                ["linear"],
                ["get", "normalized"],
                0,
                6,
                1,
                30,
              ],
              "circle-color": [
                "case",
                ["==", ["get", "above"], 1],
                "#ef4444",
                "#22d3ee",
              ],
              "circle-opacity": 0.14,
              "circle-stroke-width": 0,
            }}
          />
          <Layer
            id="stations"
            type="circle"
            filter={["==", ["get", "has_data"], 1]}
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
          <Layer
            id="stations-nodata"
            type="circle"
            filter={["==", ["get", "has_data"], 0]}
            paint={{
              "circle-radius": 4,
              "circle-color": "rgba(140,140,140,0.1)",
              "circle-stroke-color": "#5c5c5c",
              "circle-stroke-width": 1,
            }}
          />
          <Layer
            id="station-labels"
            type="symbol"
            layout={{
              "text-field": ["get", "station_code"],
              "text-size": 9,
              "text-offset": [0, 1.4],
              "text-anchor": "top",
              "text-font": ["Open Sans Regular"],
              "text-allow-overlap": false,
            }}
            paint={{
              "text-color": "#8a8a8a",
              "text-halo-color": "#0a0a0a",
              "text-halo-width": 1.5,
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
            offset={12}
            className="font-sans"
            maxWidth="340px"
          >
            <StationPopup
              props={popped.props}
              pollutantLabel={pollutant?.label ?? ""}
              pollutantUnit={pollutant?.unit ?? ""}
              threshold={threshold}
            />
          </Popup>
        )}
      </Map>

      <div className="hairline absolute left-3 top-3 flex flex-col gap-1 bg-[var(--color-surface)]/90 px-3 py-2 backdrop-blur-sm">
        <div className="label-eyebrow">Legend · {pollutant?.label ?? ""}</div>
        <div className="flex items-center gap-2 text-[0.7rem]">
          <span className="inline-block h-2.5 w-2.5 rounded-full border border-[var(--color-bg)] bg-[#ef4444]" />
          <span className="text-[var(--color-fg)]">
            above threshold · <span className="num">{stats.above}</span>
          </span>
        </div>
        <div className="flex items-center gap-2 text-[0.7rem]">
          <span className="inline-block h-2.5 w-2.5 rounded-full border border-[var(--color-bg)] bg-[#22d3ee]" />
          <span className="text-[var(--color-fg)]">
            below threshold · <span className="num">{stats.below}</span>
          </span>
        </div>
        <div className="flex items-center gap-2 text-[0.7rem]">
          <span className="inline-block h-2.5 w-2.5 rounded-full border border-[#5c5c5c] bg-transparent" />
          <span className="text-[var(--color-fg-muted)]">
            no data in window · <span className="num">{stats.missing}</span>
          </span>
        </div>
      </div>
    </div>
  );
}

function StationPopup({
  props,
  pollutantLabel,
  pollutantUnit,
  threshold,
}: {
  props: PoppedProperties;
  pollutantLabel: string;
  pollutantUnit: string;
  threshold: number;
}) {
  const hasData = props.has_data === 1 && props.value != null;
  const above = props.above === 1;
  const statusLabel =
    props.dominant_status != null
      ? STATUS_BY_CODE[props.dominant_status]?.label ??
        `code ${props.dominant_status}`
      : "—";
  return (
    <div className="min-w-[220px] space-y-2 text-[0.78rem]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="label-eyebrow">Station</div>
          <div className="num text-[1rem] font-medium text-[var(--color-fg)]">
            {props.station_code}
          </div>
        </div>
        {hasData && (
          <div
            className="hairline px-2 py-0.5 text-[0.65rem]"
            style={{
              borderColor: above ? "#ef4444" : "#22d3ee",
              color: above ? "#ef4444" : "#22d3ee",
            }}
          >
            {above ? "above" : "below"} · {pollutantLabel}
          </div>
        )}
      </div>
      {hasData ? (
        <div className="grid grid-cols-2 gap-y-1.5 border-t border-[var(--color-border)] pt-2">
          <div className="label-eyebrow">Mean</div>
          <div className="num text-right text-[var(--color-fg)]">
            {props.value!.toFixed(4)}
            <span className="ml-1 text-[0.65rem] text-[var(--color-fg-subtle)]">
              {pollutantUnit}
            </span>
          </div>
          <div className="label-eyebrow">Threshold</div>
          <div className="num text-right text-[var(--color-fg-muted)]">
            {threshold}
            <span className="ml-1 text-[0.65rem] text-[var(--color-fg-subtle)]">
              {pollutantUnit}
            </span>
          </div>
          <div className="label-eyebrow">Records</div>
          <div className="num text-right text-[var(--color-fg-muted)]">
            {props.record_count.toLocaleString()}
          </div>
          <div className="label-eyebrow">Dominant status</div>
          <div className="text-right text-[var(--color-fg-muted)]">
            {statusLabel}
          </div>
        </div>
      ) : (
        <div className="border-t border-[var(--color-border)] pt-2 text-[0.72rem] text-[var(--color-fg-muted)]">
          No {pollutantLabel} readings in the selected window. Station metadata is
          still known; check the Time Series tab for available months.
        </div>
      )}
    </div>
  );
}
