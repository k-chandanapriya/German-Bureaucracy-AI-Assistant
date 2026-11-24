import { Suspense } from "react";
import CaseView from "@/components/CaseView";

export default function Page() {
  return (
    <Suspense fallback={<p className="text-stone-500">Loading…</p>}>
      <CaseView />
    </Suspense>
  );
}
