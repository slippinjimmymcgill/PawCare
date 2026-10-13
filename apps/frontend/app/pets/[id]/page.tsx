"use client";

import { Suspense, useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiDelete, apiGet, apiPut, getStoredToken } from "@/lib/api";
import type { Pet, PetCreatePayload } from "@/lib/types";
import { formatPetAge, formatPetWeight } from "@/lib/pet-utils";
import { PetFormModal } from "@/components/pet-form-modal";
import { ArchivePetModal } from "@/components/archive-pet-modal";

interface PageProps {
  params: Promise<{ id: string }>;
}

function PetDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-44 rounded-3xl bg-slate-200" />
      <div className="grid gap-6 md:grid-cols-3">
        <div className="h-64 rounded-3xl bg-slate-200 md:col-span-2" />
        <div className="h-64 rounded-3xl bg-slate-200" />
      </div>
    </div>
  );
}

function PetDetailContent({ params }: PageProps) {
  const resolvedParams = use(params);
  const petId = resolvedParams.id;
  const router = useRouter();

  const [pet, setPet] = useState<Pet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadPet() {
      const token = getStoredToken();
      if (!token) {
        router.push("/login");
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const data = await apiGet<Pet>(`/api/v1/pets/${petId}`, token);
        if (isMounted) setPet(data);
      } catch (err: unknown) {
        if (isMounted) {
          if (err instanceof Error) {
            setError(err.message);
          } else {
            setError("Unable to load pet profile.");
          }
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadPet();

    return () => {
      isMounted = false;
    };
  }, [petId, router]);

  async function handleUpdatePet(payload: PetCreatePayload) {
    if (!pet) return;
    const token = getStoredToken();
    if (!token) throw new Error("Please log in first.");

    const updated = await apiPut<Pet>(
      `/api/v1/pets/${pet.id}`,
      payload as unknown as Record<string, unknown>,
      token
    );
    setPet(updated);
    showToast(`Saved changes for ${updated.name}.`);
  }

  async function handleArchivePet() {
    if (!pet) return;
    const token = getStoredToken();
    if (!token) throw new Error("Please log in first.");

    await apiDelete<{ status: string; message: string }>(
      `/api/v1/pets/${pet.id}`,
      token
    );
    router.push("/pets");
  }

  function showToast(msg: string) {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  }

  if (loading) {
    return <PetDetailSkeleton />;
  }

  if (error || !pet) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-12 text-center shadow-sm">
        <div className="text-3xl">⚠️</div>
        <h2 className="mt-3 text-xl font-bold text-rose-900">Pet Profile Not Found</h2>
        <p className="mt-1 text-sm text-rose-700">
          {error || "The requested pet profile does not exist or has been archived."}
        </p>
        <Link
          href="/pets"
          className="mt-6 inline-flex rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 transition"
        >
          Back to Pets List
        </Link>
      </div>
    );
  }

  const isDog = pet.species === "dog";

  return (
    <div className="space-y-8">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="rounded-2xl border border-teal-200 bg-teal-50 p-4 text-sm font-medium text-teal-800 shadow-sm animate-in fade-in duration-300">
          ✨ {toastMessage}
        </div>
      )}

      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
        <Link href="/pets" className="hover:text-slate-800 transition">
          My Pets
        </Link>
        <span>/</span>
        <span className="text-slate-900">{pet.name}</span>
      </div>

      {/* Hero Pet Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-5">
            <div
              className={`flex h-20 w-20 shrink-0 items-center justify-center rounded-3xl text-4xl shadow-inner ${
                isDog
                  ? "bg-gradient-to-br from-cyan-100 to-teal-100 text-cyan-800 ring-4 ring-cyan-50"
                  : "bg-gradient-to-br from-amber-100 to-orange-100 text-amber-800 ring-4 ring-amber-50"
              }`}
            >
              {isDog ? "🐕" : "🐈"}
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
                  {pet.name}
                </h1>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider ${
                    isDog
                      ? "bg-cyan-100 text-cyan-800 ring-1 ring-cyan-800/10"
                      : "bg-amber-100 text-amber-800 ring-1 ring-amber-800/10"
                  }`}
                >
                  {pet.species}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-500 font-medium">
                {pet.breed || "Mixed / Unknown breed"} •{" "}
                <span className="capitalize">{pet.sex}</span> •{" "}
                <span>{formatPetAge(pet.date_of_birth)}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-xs hover:bg-slate-50 hover:text-slate-900 transition"
            >
              ✏️ Edit Profile
            </button>
            <button
              type="button"
              onClick={() => setIsArchiveModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50/60 px-4 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-100 transition"
              title="Archive Pet Profile"
            >
              🗑️ Archive
            </button>
          </div>
        </div>

        {/* Quick Highlights Bar */}
        <div className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-100 pt-6 sm:grid-cols-4">
          <div className="rounded-2xl bg-slate-50/80 p-3.5">
            <span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Weight
            </span>
            <span className="text-base font-bold text-slate-800">
              {formatPetWeight(pet.weight_kg)}
            </span>
          </div>
          <div className="rounded-2xl bg-slate-50/80 p-3.5">
            <span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Age
            </span>
            <span className="text-base font-bold text-slate-800">
              {formatPetAge(pet.date_of_birth)}
            </span>
          </div>
          <div className="rounded-2xl bg-slate-50/80 p-3.5">
            <span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Date of Birth
            </span>
            <span className="text-base font-bold text-slate-800">
              {pet.date_of_birth || "Unknown"}
            </span>
          </div>
          <div className="rounded-2xl bg-slate-50/80 p-3.5">
            <span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Registered
            </span>
            <span className="text-base font-bold text-slate-800">
              {new Date(pet.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Details + Quick Care Hub */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left Column: Health Profile Details */}
        <div className="space-y-6 lg:col-span-2">
          {/* Allergies Card */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold tracking-tight text-slate-900 flex items-center gap-2">
                <span>⚠️</span> Known Allergies & Sensitivities
              </h2>
            </div>
            <div className="mt-4">
              {pet.allergies ? (
                <div className="rounded-2xl border border-rose-100 bg-rose-50/60 p-4 text-sm font-medium text-rose-800">
                  {pet.allergies}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  No known food, medication, or environmental allergies recorded.
                </p>
              )}
            </div>
          </div>

          {/* Medical History Card */}
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold tracking-tight text-slate-900 flex items-center gap-2">
                <span>📋</span> Medical History & Background
              </h2>
            </div>
            <div className="mt-4">
              {pet.medical_history ? (
                <div className="whitespace-pre-line rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700">
                  {pet.medical_history}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  No previous medical history, surgical records, or chronic condition notes entered.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Health Care Shortcuts */}
        <div className="space-y-4">
          <div className="rounded-3xl border border-slate-200 bg-gradient-to-b from-white to-slate-50/50 p-6 shadow-sm">
            <h2 className="text-base font-bold tracking-tight text-slate-900">
              Pet Health Care Hub
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Access health monitoring tools personalized for {pet.name}.
            </p>

            <div className="mt-5 space-y-3">
              {/* Health Records */}
              <Link
                href={`/pets/${pet.id}/records`}
                className="group flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs hover:border-cyan-500/50 hover:shadow-md transition"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700 text-lg">
                    📋
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-cyan-700 transition">
                      Health Records
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      Visits, vaccinations, and medications
                    </p>
                  </div>
                </div>
                <span className="text-slate-400 group-hover:text-cyan-600 group-hover:translate-x-0.5 transition">
                  →
                </span>
              </Link>

              {/* Symptom Checker */}
              <Link
                href={`/pets/${pet.id}/assess`}
                className="group flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs hover:border-cyan-500/50 hover:shadow-md transition"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50 text-rose-700 text-lg">
                    🩺
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-rose-700 transition">
                      Symptom Checker
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      Triage urgency & guidance
                    </p>
                  </div>
                </div>
                <span className="text-slate-400 group-hover:text-rose-600 group-hover:translate-x-0.5 transition">
                  →
                </span>
              </Link>

              {/* AI Assistant */}
              <Link
                href={`/pets/${pet.id}/chat`}
                className="group flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs hover:border-cyan-500/50 hover:shadow-md transition"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 text-lg">
                    💬
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-700 transition">
                      AI Health Assistant
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      RAG cited pet-care answers
                    </p>
                  </div>
                </div>
                <span className="text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition">
                  →
                </span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <PetFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSubmit={handleUpdatePet}
        initialData={pet}
        title={`Edit ${pet.name}'s Profile`}
      />

      {/* Archive Modal */}
      <ArchivePetModal
        isOpen={isArchiveModalOpen}
        petName={pet.name}
        onClose={() => setIsArchiveModalOpen(false)}
        onConfirm={handleArchivePet}
      />
    </div>
  );
}

export default function PetDetailPage({ params }: PageProps) {
  return (
    <Suspense fallback={<PetDetailSkeleton />}>
      <PetDetailContent params={params} />
    </Suspense>
  );
}
