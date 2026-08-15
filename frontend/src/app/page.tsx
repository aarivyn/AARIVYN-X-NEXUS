"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthed } from "@/lib/store";

export default function Home() {
  const router = useRouter();
  const authed = useAuthed();

  useEffect(() => {
    router.replace(authed ? "/app/workspace" : "/login");
  }, [authed, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-600 text-xl font-bold text-white">
          NX
        </div>
        <div className="animate-pulse text-sm text-slate-400">Loading NEXUS…</div>
      </div>
    </div>
  );
}
