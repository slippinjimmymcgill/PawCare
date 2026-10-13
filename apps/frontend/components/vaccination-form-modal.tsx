"use client";

import { useState } from "react";
import type { Vaccination, VaccinationPayload } from "@/lib/types";

interface VaccinationFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: VaccinationPayload) => Promise<void>;
  initialData?: Vaccination | null;
}

export function VaccinationFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
}: VaccinationFormModalProps) {
  const [vaccineName, setVaccineName] = useState(initialData?.vaccine_name || "");
  const [administeredDate, setAdministeredDate] = useState(
    initialData?.administered_date || new Date().toISOString().split("T")[0]
  );
  const [nextDueDate, setNextDueDate] = useState(initialData?.next_due_date || "");
  const [notes, setNotes] = useState(initialData?.notes || "");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!vaccineName.trim()) {
      setError("Vaccine name is required.");
      return;
    }

    try {
      setLoading(true);
      await onSubmit({
        vaccine_name: vaccineName.trim(),
        administered_date: administeredDate || null,
        next_due_date: nextDueDate || null,
        notes: notes.trim() || null,
      });
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to save vaccination record.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl sm:p-8">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">
              {initialData ? "Edit Vaccination" : "Log New Vaccination"}
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Record immunizations and upcoming booster dates for automatic reminders.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Vaccine Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={vaccineName}
              onChange={(e) => setVaccineName(e.target.value)}
              placeholder="e.g. Rabies 3-Year, DHPP (Distemper), Bordetella, FVRCP"
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Date Administered
              </label>
              <input
                type="date"
                value={administeredDate}
                onChange={(e) => setAdministeredDate(e.target.value)}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Next Due Date
              </label>
              <input
                type="date"
                value={nextDueDate}
                onChange={(e) => setNextDueDate(e.target.value)}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Notes & Certification
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Tag #8912 issued, administered by City Vet clinic, no adverse reaction"
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition disabled:opacity-50"
            >
              {loading ? "Saving..." : initialData ? "Save Changes" : "Record Vaccine"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
