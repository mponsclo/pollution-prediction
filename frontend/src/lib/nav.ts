import {
  Activity,
  AlertTriangle,
  Gauge,
  LineChart,
  Map as MapIcon,
  Sigma,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
};

export const NAV_ITEMS: NavItem[] = [
  {
    href: "/timeseries",
    label: "Time Series",
    description: "Pollutant concentration over time by station.",
    icon: LineChart,
  },
  {
    href: "/geo",
    label: "Geographic",
    description: "Station locations and threshold exceedances on a map.",
    icon: MapIcon,
  },
  {
    href: "/quality",
    label: "Data Quality",
    description: "Missingness, status availability, monthly trends.",
    icon: Gauge,
  },
  {
    href: "/stats",
    label: "Statistics",
    description: "Distributions, percentiles, inter-station correlation.",
    icon: Sigma,
  },
  {
    href: "/forecasts",
    label: "Forecasts",
    description: "48h-ahead predictions with 90% intervals.",
    icon: TrendingUp,
  },
  {
    href: "/anomalies",
    label: "Anomalies",
    description: "Supervised LightGBM anomaly detection.",
    icon: AlertTriangle,
  },
];

export const HOME_NAV: NavItem = {
  href: "/",
  label: "Overview",
  description: "Project overview.",
  icon: Activity,
};
