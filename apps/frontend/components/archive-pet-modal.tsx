"use client";

import { useState } from "react";

interface ArchivePetModalProps {
  isOpen: boolean;
  petName: string;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export function ArchivePetModal({
  isOpen,
  petName,
  onClose,
  onConfirm,
}: ArchivePetModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleArchive() {
    try {
      setLoading(true);
      setError(null);
      await onConfirm();
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to archive pet.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 text-xl font-bold">
          ⚠️
        </div>

        <h3 className="mt-4 text-lg font-bold tracking-tight text-slate-900">
          Archive {petName}&apos;s Profile?
        </h3>

        <div className="mt-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-xs text-slate-600 leading-relaxed space-y-2">
          <p>
            <strong>Soft-Delete Policy:</strong> Archiving will remove{" "}
            <span className="font-semibold text-slate-800">{petName}</span> from your active pets list.
          </p>
          <p>
            Historical records, vaccinations, and previous symptom assessments remain preserved in accordance with PawCare data retention policies.
          </p>
        </div>

        {error && (
          <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            {error}
          </div>
        )}

        <div className="mt-6 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 transition disabled:opacity-50"
          >
            Keep Active
          </button>
          <button
            type="button"
            onClick={handleArchive}
            disabled={loading}
            className="rounded-xl bg-amber-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-amber-700 transition disabled:opacity-50"
          >
            {loading ? "Archiving..." : "Confirm Archive"}
          </button>
        </div>
      </div>
    </div>
  );
}
