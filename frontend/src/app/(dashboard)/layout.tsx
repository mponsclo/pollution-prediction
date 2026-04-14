import { Suspense } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { GlobalFilters } from "@/components/filters/GlobalFilters";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <Suspense fallback={<div className="hairline-b h-11" />}>
          <GlobalFilters />
        </Suspense>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
