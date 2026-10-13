"use client";

import { useState } from "react";
import type { Pet, PetCreatePayload, PetSex, PetSpecies } from "@/lib/types";

interface PetFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: PetCreatePayload) => Promise<void>;
  initialData?: Pet | null;
  title: string;
}

export function PetFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  title,
}: PetFormModalProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [species, setSpecies] = useState<PetSpecies>(initialData?.species || "dog");
  const [breed, setBreed] = useState(initialData?.breed || "");
  const [sex, setSex] = useState<PetSex>(initialData?.sex || "unknown");
  const [dateOfBirth, setDateOfBirth] = useState(initialData?.date_of_birth || "");
  const [weightKg, setWeightKg] = useState<string>(
    initialData?.weight_kg !== null && initialData?.weight_kg !== undefined
      ? String(initialData.weight_kg)
      : ""
  );
  const [allergies, setAllergies] = useState(initialData?.allergies || "");
  const [medicalHistory, setMedicalHistory] = useState(initialData?.medical_history || "");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Pet name is required.");
      return;
    }

    let parsedWeight: number | null = null;
    if (weightKg.trim()) {
      parsedWeight = parseFloat(weightKg);
      if (isNaN(parsedWeight) || parsedWeight <= 0 || parsedWeight > 200) {
        setError("Please enter a valid weight between 0.1 and 200 kg.");
        return;
      }
    }

    const payload: PetCreatePayload = {
      name: name.trim(),
      species,
      breed: breed.trim() || null,
      sex,
      date_of_birth: dateOfBirth || null,
      weight_kg: parsedWeight,
      allergies: allergies.trim() || null,
      medical_history: medicalHistory.trim() || null,
    };

    try {
      setLoading(true);
      await onSubmit(payload);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred while saving pet profile.");
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
            <h2 className="text-xl font-bold tracking-tight text-slate-900">{title}</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter your pet&apos;s details to personalize health tracking and AI advice.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm text-rose-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Pet Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Milo, Luna, Buddy"
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Species <span className="text-rose-500">*</span>
              </label>
              <div className="mt-1.5 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSpecies("dog")}
                  className={`flex items-center justify-center gap-1.5 rounded-xl border py-2 text-sm font-medium transition ${
                    species === "dog"
                      ? "border-cyan-600 bg-cyan-50/80 text-cyan-800 font-semibold ring-1 ring-cyan-600"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span>🐕</span> Dog
                </button>
                <button
                  type="button"
                  onClick={() => setSpecies("cat")}
                  className={`flex items-center justify-center gap-1.5 rounded-xl border py-2 text-sm font-medium transition ${
                    species === "cat"
                      ? "border-amber-600 bg-amber-50/80 text-amber-800 font-semibold ring-1 ring-amber-600"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span>🐈</span> Cat
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Sex
              </label>
              <select
                value={sex}
                onChange={(e) => setSex(e.target.value as PetSex)}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Breed
              </label>
              <input
                type="text"
                value={breed}
                onChange={(e) => setBreed(e.target.value)}
                placeholder="e.g. Golden Retriever"
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Weight (kg)
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="200"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                placeholder="e.g. 15.2"
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Date of Birth
            </label>
            <input
              type="date"
              max={new Date().toISOString().split("T")[0]}
              value={dateOfBirth}
              onChange={(e) => setDateOfBirth(e.target.value)}
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Known Allergies
            </label>
            <input
              type="text"
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              placeholder="e.g. Beef, chicken, flea bites, penicillin"
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Medical History
            </label>
            <textarea
              rows={2}
              value={medicalHistory}
              onChange={(e) => setMedicalHistory(e.target.value)}
              placeholder="e.g. Spayed/neutered in 2023, recovered from kennel cough, prone to skin allergies"
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
              {loading ? "Saving..." : initialData ? "Save Changes" : "Create Profile"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
