"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import LetterResult from "@/components/LetterResult";
import { api, type LetterCard, type Meta } from "@/lib/api";

export default function LetterView() {
  const id = useSearchParams().get("id") ?? "";
  const [card, setCard] = useState<LetterCard | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.letter(id), api.meta()])
      .then(([c, m]) => {
        setCard(c);
        setMeta(m);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p className="text-red-700">{error}</p>;
  if (!card) return <p className="text-ink/55">Loading…</p>;
  return <LetterResult key={card.letter_id} initial={card} meta={meta} />;
}
