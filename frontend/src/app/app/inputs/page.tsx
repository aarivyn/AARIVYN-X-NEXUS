"use client";

import { useState } from "react";
import { Tabs } from "@/components/ui";
import { BudgetPanel } from "@/components/inputs/BudgetPanel";
import { LocationsPanel } from "@/components/inputs/LocationsPanel";
import { SocialPanel } from "@/components/inputs/SocialPanel";
import { TimelinePanel } from "@/components/inputs/TimelinePanel";
import { MapIngestPanel } from "@/components/inputs/MapIngestPanel";

const TABS = [
  { id: "budget", label: "💰 Budget" },
  { id: "locations", label: "📍 Locations" },
  { id: "social", label: "👥 Social groups" },
  { id: "timeline", label: "⏱️ Timeline" },
  { id: "maps", label: "🗂️ Map data ingest" },
];

export default function InputsPage() {
  const [tab, setTab] = useState("budget");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Project inputs</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">
          Define the constraints and context for the analysis. Site data ingested here
          <span className="font-medium text-slate-700"> takes precedence</span> over request
          defaults across every downstream module — budget caps, timelines, social context and
          community units all flow into feasibility, optimization and provenance.
        </p>
      </div>

      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === "budget" && <BudgetPanel />}
      {tab === "locations" && <LocationsPanel />}
      {tab === "social" && <SocialPanel />}
      {tab === "timeline" && <TimelinePanel />}
      {tab === "maps" && <MapIngestPanel />}
    </div>
  );
}
