"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { RunPanel } from "@/components/analysis/RunPanel";
import { ResultTabs } from "@/components/analysis/ResultTabs";
import { useApp } from "@/lib/store";
import { Alert, Button, Card, EmptyState } from "@/components/ui";
import type { NexusJobStatus } from "@/lib/types";

export default function AnalysisPage() {
  const { result, job, setResult } = useApp();
  const [autoAdvanced, setAutoAdvanced] = useState(false);
  const router = useRouter();

  const handleDone = useCallback(
    (j: NexusJobStatus) => {
      if (j.result) {
        setResult(j.result);
        // Once complete, let the user advance; highlight next step.
        setAutoAdvanced(true);
      }
    },
    [setResult]
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Analysis pipeline</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">
          Runs Modules 2–7 end-to-end: Earth observation ingestion → water intelligence → problem
          detection & context → intervention knowledge graph → feasibility → NSGA-II optimization →
          implementation plan. Results feed the remaining steps automatically.
        </p>
      </div>

      <RunPanel onDone={handleDone} />

      {result ? (
        <div className="space-y-4">
          {autoAdvanced && (
            <Alert tone="success" title="Analysis complete">
              The pipeline produced feasibility, Pareto portfolios and an implementation plan. Continue to{" "}
              <button className="font-semibold underline" onClick={() => router.push("/app/feasibility")}>
                Feasibility & Optimize →
              </button>{" "}
              or review the detailed outputs below.
            </Alert>
          )}
          <ResultTabs result={result} />
        </div>
      ) : job?.status === "FAILED" ? (
        <Card title="No results" icon={<span>⚠️</span>}>
          <EmptyState title="The pipeline job failed" body="Check the job card above for the error message, adjust the configuration and re-run." />
        </Card>
      ) : (
        <Card title="No results yet" icon={<span>📭</span>}>
          <EmptyState
            title="Run the pipeline to generate analysis results"
            body="Configure the inputs above (or use defaults from your workspace and ingested site data), then press “Run NEXUS analysis”. Live stage progress appears here; completed results populate the tabs below and unlock the next steps."
          />
          <div className="mt-4 flex gap-2">
            <Button variant="secondary" onClick={() => router.push("/app/inputs")}>← Back to inputs</Button>
          </div>
        </Card>
      )}
    </div>
  );
}
