"use client";

import { useEffect, useState } from "react";
import { api, type Draft, type LetterCard, type ReplyTemplate } from "@/lib/api";

const PROFILE_KEY = "amtspost.profile";

interface Profile {
  name: string;
  address: string;
  city: string;
}

export default function ReplyDrafter({
  template,
  card,
  onClose,
}: {
  template: ReplyTemplate;
  card: LetterCard;
  onClose: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Only rendered after a click, so localStorage is available.
  const [profile, setProfile] = useState<Profile>(() => {
    const saved = localStorage.getItem(PROFILE_KEY);
    return saved ? JSON.parse(saved) : { name: "", address: "", city: "" };
  });
  const [recipient, setRecipient] = useState(card.sender.address || card.sender.name);

  useEffect(() => {
    api.prefill(template.id, card.letter_id).then(setValues).catch(() => {});
  }, [template.id, card.letter_id]);

  const generate = async () => {
    setError(null);
    try {
      setDraft(await api.draft(template.id, values, card.letter_id));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const downloadPdf = async () => {
    if (!draft) return;
    if (!profile.name || !profile.address || !profile.city || !recipient) {
      setError("Fill in your name, address, city and the recipient address for the letter.");
      return;
    }
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    try {
      const blob = await api.pdf({
        subject_de: draft.subject_de,
        body_de: draft.body_de,
        sender_name: profile.name,
        sender_address: profile.address,
        recipient_address: recipient,
        city: profile.city,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${template.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4">
      <div className="card my-8 w-full max-w-4xl space-y-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-light">{template.title}</h2>
            <p className="mono-label mt-2 border-l-2 border-accent pl-2 normal-case tracking-normal text-ink/70">{template.channel}</p>
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>

        {!draft ? (
          <div className="space-y-3">
            {template.fields.map((f) => (
              <label key={f.name} className="block">
                <span className="label">
                  {f.label}
                  {!f.required && " (optional)"}
                </span>
                {f.multiline ? (
                  <textarea
                    className="input min-h-24"
                    value={values[f.name] ?? ""}
                    placeholder={f.placeholder}
                    onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
                  />
                ) : (
                  <input
                    className="input"
                    value={values[f.name] ?? ""}
                    placeholder={f.placeholder}
                    onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
                  />
                )}
              </label>
            ))}
            {error && <p className="text-sm text-red-700">{error}</p>}
            <button className="btn-primary" onClick={generate}>
              Draft the letter
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="bg-paper p-4">
                <p className="label">German (this is what you send)</p>
                <p className="font-medium">{draft.subject_de}</p>
                <p className="mt-3 whitespace-pre-wrap text-sm">Sehr geehrte Damen und Herren,{"\n\n"}{draft.body_de}{"\n\n"}Mit freundlichen Grüßen</p>
              </div>
              <div className="border border-dashed border-ink/25 p-4">
                <p className="label">English (so you know what you sign)</p>
                <p className="whitespace-pre-wrap text-sm text-ink/75">{draft.body_en}</p>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label>
                <span className="label">Your name</span>
                <input className="input" value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} />
              </label>
              <label>
                <span className="label">Your city (for the date line)</span>
                <input className="input" value={profile.city} onChange={(e) => setProfile({ ...profile, city: e.target.value })} />
              </label>
              <label>
                <span className="label">Your address</span>
                <textarea
                  className="input min-h-20"
                  placeholder={"Musterstraße 1\n10115 Berlin"}
                  value={profile.address}
                  onChange={(e) => setProfile({ ...profile, address: e.target.value })}
                />
              </label>
              <label>
                <span className="label">Recipient address</span>
                <textarea className="input min-h-20" value={recipient} onChange={(e) => setRecipient(e.target.value)} />
              </label>
            </div>
            {error && <p className="text-sm text-red-700">{error}</p>}
            <div className="flex flex-wrap gap-2">
              <button className="btn-primary" onClick={downloadPdf}>
                Download PDF (DIN 5008)
              </button>
              <button className="btn-secondary" onClick={() => navigator.clipboard.writeText(`${draft.subject_de}\n\nSehr geehrte Damen und Herren,\n\n${draft.body_de}\n\nMit freundlichen Grüßen\n${profile.name}`)}>
                Copy text
              </button>
              <button className="btn-secondary" onClick={() => setDraft(null)}>
                Edit fields
              </button>
            </div>
            <p className="text-xs text-ink/55">
              Print, sign by hand and keep a copy. This template gives you the form; whether to appeal is your decision. If in doubt,
              ask a Steuerberater, Lohnsteuerhilfeverein or lawyer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
