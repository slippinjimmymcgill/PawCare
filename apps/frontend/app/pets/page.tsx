"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiDelete, apiGet, apiPost, apiPut, getStoredToken } from "@/lib/api";
import type { Pet, PetCreatePayload } from "@/lib/types";
import { PetCard } from "@/components/pet-card";
import { PetFormModal } from "@/components/pet-form-modal";
import { ArchivePetModal } from "@/components/archive-pet-modal";

export default function PetsPage() {
  const [pets, setPets] = useState<Pet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingPet, setEditingPet] = useState<Pet | null>(null);
  const [archivingPet, setArchivingPet] = useState<Pet | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  useEffect(() => {
    loadPets();
  }, []);

  async function loadPets() {
    const token = getStoredToken();
    if (!token) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    setIsAuthenticated(true);
    setLoading(true);
    setError(null);

    try {
      const data = await apiGet<Pet[]>("/api/v1/pets", token);
      setPets(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not load pets. Please ensure the backend is running.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleCreatePet(payload: PetCreatePayload) {
    const token = getStoredToken();
    if (!token) throw new Error("Please log in first.");

    const created = await apiPost<Pet>("/api/v1/pets", payload as unknown as Record<string, unknown>, token);
    setPets((prev) => [created, ...prev]);
    showFeedback(`Successfully added ${created.name}!`);
  }

  async function handleUpdatePet(payload: PetCreatePayload) {
    if (!editingPet) return;
    const token = getStoredToken();
    if (!token) throw new Error("Please log in first.");

    const updated = await apiPut<Pet>(
      `/api/v1/pets/${editingPet.id}`,
      payload as unknown as Record<string, unknown>,
      token
    );
    setPets((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    showFeedback(`Updated ${updated.name}'s profile.`);
  }

  async function handleArchivePet() {
    if (!archivingPet) return;
    const token = getStoredToken();
    if (!token) throw new Error("Please log in first.");

    await apiDelete<{ status: string; message: string }>(
      `/api/v1/pets/${archivingPet.id}`,
      token
    );
    setPets((prev) => prev.filter((p) => p.id !== archivingPet.id));
    showFeedback(`Archived ${archivingPet.name}. Records remain preserved.`);
  }

  function showFeedback(msg: string) {
    setFeedbackMessage(msg);
    setTimeout(() => {
      setFeedbackMessage(null);
    }, 4000);
  }

  return (
    <div className="space-y-8">
      {/* Top Banner & Action */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700 ring-1 ring-cyan-700/10">
            <span>🐾</span> Multi-Pet Profiles
          </div>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            My Pets
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Keep track of health records, medications, and personalized AI care for your companions.
          </p>
        </div>

        {isAuthenticated && (
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-cyan-600/25 transition hover:from-cyan-700 hover:to-teal-700 hover:shadow-cyan-600/35"
          >
            <span className="text-base font-bold">+</span> Add New Pet
          </button>
        )}
      </div>

      {/* Temporary Success Toast */}
      {feedbackMessage && (
        <div className="rounded-2xl border border-teal-200 bg-teal-50 p-4 text-sm font-medium text-teal-800 shadow-sm animate-in fade-in duration-300">
          ✨ {feedbackMessage}
        </div>
      )}

      {/* Unauthenticated State */}
      {isAuthenticated === false && (
        <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-sm">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-cyan-50 text-3xl">
            🔐
          </div>
          <h2 className="mt-4 text-xl font-bold tracking-tight text-slate-900">
            Authentication Required
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
            Log in to view your pets, manage medical histories, and run AI health checks.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              href="/login"
              className="rounded-xl bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-cyan-700 transition"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
            >
              Register
            </Link>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && isAuthenticated && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-72 animate-pulse rounded-3xl border border-slate-100 bg-white p-6 shadow-sm"
            >
              <div className="flex gap-3">
                <div className="h-12 w-12 rounded-2xl bg-slate-100" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-24 rounded-sm bg-slate-100" />
                  <div className="h-3 w-36 rounded-sm bg-slate-100" />
                </div>
              </div>
              <div className="mt-6 h-14 rounded-2xl bg-slate-50" />
              <div className="mt-8 h-9 rounded-xl bg-slate-100" />
            </div>
          ))}
        </div>
      )}

      {/* Error Alert */}
      {error && !loading && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-800">
          <p className="font-semibold">{error}</p>
          <button
            type="button"
            onClick={loadPets}
            className="mt-3 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-700 transition"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && isAuthenticated && pets.length === 0 && !error && (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-xs">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-slate-50 text-4xl shadow-inner">
            🐶🐱
          </div>
          <h2 className="mt-4 text-xl font-bold tracking-tight text-slate-900">
            No pets registered yet
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
            Add your dog or cat to get started with health monitoring, immunization schedules, and symptom triage.
          </p>
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-cyan-700 transition"
          >
            <span>+</span> Register Your First Pet
          </button>
        </div>
      )}

      {/* Pets Grid */}
      {!loading && isAuthenticated && pets.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {pets.map((pet) => (
            <PetCard
              key={pet.id}
              pet={pet}
              onEditClick={(p) => setEditingPet(p)}
              onArchiveClick={(p) => setArchivingPet(p)}
            />
          ))}
        </div>
      )}

      {/* Create Pet Modal */}
      <PetFormModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSubmit={handleCreatePet}
        title="Add New Pet Profile"
      />

      {/* Edit Pet Modal */}
      {editingPet && (
        <PetFormModal
          isOpen={true}
          onClose={() => setEditingPet(null)}
          onSubmit={handleUpdatePet}
          initialData={editingPet}
          title={`Edit ${editingPet.name}'s Profile`}
        />
      )}

      {/* Archive Confirmation Modal */}
      {archivingPet && (
        <ArchivePetModal
          isOpen={true}
          petName={archivingPet.name}
          onClose={() => setArchivingPet(null)}
          onConfirm={handleArchivePet}
        />
      )}
    </div>
  );
}
