import { PanelSkeleton, MetricStripSkeleton } from "@/components/ui/Skeleton";

export default function DashboardLoading() {
  return (
    <div className="flex flex-col gap-px bg-[var(--color-border)]">
      <div className="bg-[var(--color-bg)] p-6">
        <MetricStripSkeleton />
      </div>
      <div className="grid grid-cols-12 gap-px bg-[var(--color-border)]">
        <div className="col-span-12 bg-[var(--color-bg)] p-6 xl:col-span-8">
          <PanelSkeleton title="Fetching from BigQuery…" height={420} />
        </div>
        <div className="col-span-12 flex flex-col gap-px bg-[var(--color-border)] xl:col-span-4">
          <div className="bg-[var(--color-bg)] p-6 pb-3">
            <PanelSkeleton title="Loading panel" height={180} />
          </div>
          <div className="bg-[var(--color-bg)] p-6 pt-3">
            <PanelSkeleton title="Loading panel" height={180} />
          </div>
        </div>
      </div>
    </div>
  );
}
