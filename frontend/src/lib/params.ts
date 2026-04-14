import {
  DEFAULT_POLLUTANT_CODE,
  DEFAULT_RANGE,
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
  const stations = stationsRaw
    ? stationsRaw
        .split(",")
        .map((s) => Number(s))
        .filter((n) => STATION_CODES.includes(n))
    : STATION_CODES;

  const start = get("start") ?? DEFAULT_RANGE.start;
  const end = get("end") ?? DEFAULT_RANGE.end;

  return {
    pollutantCode,
    stations: stations.length > 0 ? stations : STATION_CODES,
    start,
    end,
  };
}
