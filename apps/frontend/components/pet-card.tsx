"use client";

import Link from "next/link";
import type { Pet } from "@/lib/types";
import { formatPetAge, formatPetWeight } from "@/lib/pet-utils";

interface PetCardProps {
  pet: Pet;
  onEditClick: (pet: Pet) => void;
  onArchiveClick: (pet: Pet) => void;
}

export function PetCard({ pet, onEditClick, onArchiveClick }: PetCardProps) {
  const isDog = pet.species === "dog";

  return (
    <div className="group relative flex flex-col justify-between rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-cyan-500/30 hover:shadow-xl hover:shadow-cyan-900/5">
      <div>
        {/* Header with species badge and menu */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-2xl text-2xl shadow-inner ${
                isDog
                  ? "bg-gradient-to-br from-cyan-50 to-teal-100/70 text-cyan-800"
                  : "bg-gradient-to-br from-amber-50 to-orange-100/70 text-amber-800"
              }`}
            >
              {isDog ? "🐕" : "🐈"}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold tracking-tight text-slate-900 group-hover:text-cyan-700 transition">
                  {pet.name}
                </h3>
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                    isDog
                      ? "bg-cyan-50 text-cyan-700 ring-1 ring-cyan-700/10"
                      : "bg-amber-50 text-amber-700 ring-1 ring-amber-700/10"
                  }`}
                >
                  {pet.species}
                </span>
              </div>
              <p className="text-xs font-medium text-slate-500">
                {pet.breed || "Mixed / Unknown breed"} •{" "}
                <span className="capitalize">{pet.sex}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1 opacity-90">
            <button
              type="button"
              onClick={() => onEditClick(pet)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
              title="Edit Profile"
              aria-label="Edit Profile"
            >
              ✏️
            </button>
            <button
              type="button"
              onClick={() => onArchiveClick(pet)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition"
              title="Archive Pet"
              aria-label="Archive Pet"
            >
              🗑️
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="mt-5 grid grid-cols-2 gap-2.5 rounded-2xl border border-slate-100 bg-slate-50/70 p-3 text-xs">
          <div>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Age
            </span>
            <span className="font-semibold text-slate-800">
              {formatPetAge(pet.date_of_birth)}
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Weight
            </span>
            <span className="font-semibold text-slate-800">
              {formatPetWeight(pet.weight_kg)}
            </span>
          </div>
        </div>

        {/* Allergies & Medical History Notes */}
        {(pet.allergies || pet.medical_history) && (
          <div className="mt-3.5 space-y-1.5">
            {pet.allergies && (
              <div className="flex items-center gap-1.5 text-xs text-rose-700 bg-rose-50/70 border border-rose-100 rounded-xl px-2.5 py-1">
                <span className="text-[10px] font-bold uppercase tracking-wider">Allergies:</span>
                <span className="truncate">{pet.allergies}</span>
              </div>
            )}
            {pet.medical_history && (
              <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-100/70 border border-slate-200/50 rounded-xl px-2.5 py-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">History:</span>
                <span className="truncate">{pet.medical_history}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation Shortcuts */}
      <div className="mt-6 border-t border-slate-100 pt-4 space-y-2">
        <Link
          href={`/pets/${pet.id}`}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-cyan-700"
        >
          View Full Profile
        </Link>
        <div className="grid grid-cols-3 gap-1.5 text-center text-[11px] font-semibold text-slate-600">
          <Link
            href={`/pets/${pet.id}/records`}
            className="rounded-lg border border-slate-200 bg-slate-50/50 py-1.5 hover:border-slate-300 hover:bg-slate-100 transition"
          >
            📋 Records
          </Link>
          <Link
            href={`/pets/${pet.id}/assess`}
            className="rounded-lg border border-slate-200 bg-slate-50/50 py-1.5 hover:border-slate-300 hover:bg-slate-100 transition"
          >
            🩺 Triage
          </Link>
          <Link
            href={`/pets/${pet.id}/chat`}
            className="rounded-lg border border-slate-200 bg-slate-50/50 py-1.5 hover:border-slate-300 hover:bg-slate-100 transition"
          >
            💬 Chat
          </Link>
        </div>
      </div>
    </div>
  );
}
