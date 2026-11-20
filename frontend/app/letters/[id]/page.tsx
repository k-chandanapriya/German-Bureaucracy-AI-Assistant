import { Suspense } from "react";
import LetterView from "@/components/LetterView";

export default function Page() {
  return (
    <Suspense fallback={<p className="text-stone-500">Loading…</p>}>
      <LetterView />
    </Suspense>
  );
}
