import {
  DEFAULT_POLLUTANT_CODE,
  DEFAULT_RANGE,
  DEFAULT_STATIONS,
  POLLUTANT_BY_CODE,
  STATION_CODES,
} from "./constants";

export type DashboardParams = {
  pollutantCode: number;
  stations: number[];
  start: string;
  end: string;
};

export function parseDashboardParams(
  searchParams: URLSearchParams | Record<string, string | string[] | undefined>,
): DashboardParams {
  const get = (key: string): string | undefined => {
    if (searchParams instanceof URLSearchParams) {
      return searchParams.get(key) ?? undefined;
    }
    const v = searchParams[key];
    if (Array.isArray(v)) return v[0];
    return v;
  };

  const pollutantRaw = get("pollutant");
  const pollutantCode =
    pollutantRaw && POLLUTANT_BY_CODE[Number(pollutantRaw)]
      ? Number(pollutantRaw)
      : DEFAULT_POLLUTANT_CODE;

  const stationsRaw = get("stations");
  let stations: number[];
  if (stationsRaw === "none") {
    stations = [];
  } else if (stationsRaw) {
    const parsed = stationsRaw
      .split(",")
      .map((s) => Number(s))
      .filter((n) => STATION_CODES.includes(n));
    stations = parsed.length > 0 ? parsed : DEFAULT_STATIONS;
  } else {
    stations = DEFAULT_STATIONS;
  }

  const start = get("start") ?? DEFAULT_RANGE.start;
  const end = get("end") ?? DEFAULT_RANGE.end;

  return {
    pollutantCode,
    stations,
    start,
    end,
  };
}
