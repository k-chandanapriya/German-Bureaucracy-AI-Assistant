"use client";

import { useSyncExternalStore } from "react";

const STORAGE_KEY = "amtspost.bundesland";
const EVENT = "amtspost-bundesland";

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb);
  window.addEventListener(EVENT, cb);
  return () => {
    window.removeEventListener("storage", cb);
    window.removeEventListener(EVENT, cb);
  };
}

/** The user's Bundesland, remembered in localStorage. */
export function useBundesland(fallback = "BE") {
  const land = useSyncExternalStore(
    subscribe,
    () => localStorage.getItem(STORAGE_KEY) ?? fallback,
    () => fallback,
  );
  const update = (v: string) => {
    localStorage.setItem(STORAGE_KEY, v);
    window.dispatchEvent(new Event(EVENT));
  };
  return [land, update] as const;
}

export default function BundeslandSelect({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: Record<string, string>;
}) {
  return (
    <label className="block">
      <span className="label">Your state (public holidays differ)</span>
      <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
        {Object.entries(options).map(([code, name]) => (
          <option key={code} value={code}>
            {name}
          </option>
        ))}
      </select>
    </label>
  );
}
