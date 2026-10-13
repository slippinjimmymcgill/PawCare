"use client";

import { Suspense, useCallback, useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  getAttachmentUrl,
  getStoredToken,
} from "@/lib/api";
import type {
  HealthRecord,
  HealthRecordPayload,
  Medication,
  MedicationPayload,
  Pet,
  Vaccination,
  VaccinationPayload,
} from "@/lib/types";
import { RecordFormModal } from "@/components/record-form-modal";
import { VaccinationFormModal } from "@/components/vaccination-form-modal";
import { MedicationFormModal } from "@/components/medication-form-modal";

interface PageProps {
  params: Promise<{ id: string }>;
}

function fmtDate(iso: string | null | undefined) {
  if (!iso) return "—";
  const d = new Date(iso.includes("T") ? iso : iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function recordTypeLabel(type: string) {
  if (type === "visit") return { label: "Vet Visit", emoji: "🏥", color: "cyan" };
  if (type === "weight_log") return { label: "Weight Log", emoji: "⚖️", color: "violet" };
  return { label: "Care Note", emoji: "📝", color: "amber" };
}

function isMedActive(med: Medication) {
  const today = new Date().toISOString().split("T")[0];
  if (med.end_date && med.end_date < today) return false;
  return true;
}

function isVaxDue(vax: Vaccination) {
  if (!vax.next_due_date) return false;
  const today = new Date().toISOString().split("T")[0];
  return vax.next_due_date <= today;
}

function RecordsSkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      <div className="h-10 rounded-2xl bg-slate-200 w-2/3" />
      <div className="h-12 rounded-2xl bg-slate-200" />
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-2xl bg-slate-200" />
        ))}
      </div>
    </div>
  );
}

function Toast({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border border-teal-200 bg-white px-5 py-3.5 shadow-xl animate-in slide-in-from-bottom-4 duration-300">
      <span className="text-base">OK</span>
      <p className="text-sm font-medium text-slate-800">{message}</p>
      <button onClick={onDismiss} className="ml-2 text-slate-400 hover:text-slate-600 text-xs font-semibold">x</button>
    </div>
  );
}

function EmptyState({ icon, title, subtitle, action }: { icon: string; title: string; subtitle: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-5xl mb-4 opacity-60">{icon}</div>
      <h3 className="text-base font-semibold text-slate-700">{title}</h3>
      <p className="mt-1 text-sm text-slate-400 max-w-xs">{subtitle}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

type TimelineItem =
  | { kind: "record"; data: HealthRecord; date: string }
  | { kind: "vaccination"; data: Vaccination; date: string }
  | { kind: "medication"; data: Medication; date: string };

type TabId = "timeline" | "records" | "vaccinations" | "medications";
function RecordsContent({ params }: PageProps) {
  const resolvedParams = use(params);
  const petId = resolvedParams.id;
  const router = useRouter();

  const [pet, setPet] = useState<Pet | null>(null);
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("timeline");

  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<HealthRecord | null>(null);
  const [isVaxModalOpen, setIsVaxModalOpen] = useState(false);
  const [editingVax, setEditingVax] = useState<Vaccination | null>(null);
  const [isMedModalOpen, setIsMedModalOpen] = useState(false);
  const [editingMed, setEditingMed] = useState<Medication | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const token = typeof window !== "undefined" ? getStoredToken() : null;

  const loadAll = useCallback(async () => {
    const storedToken = getStoredToken();
    if (!storedToken) { router.push("/login"); return; }
    setLoading(true);
    setError(null);
    try {
      const [petData, recData, vaxData, medData] = await Promise.all([
        apiGet<Pet>(`/api/v1/pets/${petId}`, storedToken),
        apiGet<HealthRecord[]>(`/api/v1/records/pets/${petId}/health-records`, storedToken),
        apiGet<Vaccination[]>(`/api/v1/records/pets/${petId}/vaccinations`, storedToken),
        apiGet<Medication[]>(`/api/v1/records/pets/${petId}/medications`, storedToken),
      ]);
      setPet(petData);
      setHealthRecords(recData);
      setVaccinations(vaxData);
      setMedications(medData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load health records.");
    } finally {
      setLoading(false);
    }
  }, [petId, router]);

  useEffect(() => { loadAll(); }, [loadAll]);

  async function handleSaveRecord(payload: HealthRecordPayload) {
    const storedToken = getStoredToken();
    if (!storedToken) throw new Error("Not authenticated.");
    if (editingRecord) {
      const updated = await apiPut<HealthRecord>(
        `/api/v1/records/pets/${petId}/health-records/${editingRecord.id}`,
        payload as unknown as Record<string, unknown>,
        storedToken
      );
      setHealthRecords((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setToast("Health record updated.");
    } else {
      const created = await apiPost<HealthRecord>(
        `/api/v1/records/pets/${petId}/health-records`,
        payload as unknown as Record<string, unknown>,
        storedToken
      );
      setHealthRecords((prev) => [created, ...prev]);
      setToast("Health record added.");
    }
    setEditingRecord(null);
  }

  async function handleDeleteRecord(id: string) {
    const storedToken = getStoredToken();
    if (!storedToken) return;
    if (!confirm("Delete this health record? This cannot be undone.")) return;
    setDeletingId(id);
    try {
      await apiDelete(`/api/v1/records/pets/${petId}/health-records/${id}`, storedToken);
      setHealthRecords((prev) => prev.filter((r) => r.id !== id));
      setToast("Record deleted.");
    } catch { setToast("Failed to delete record."); }
    finally { setDeletingId(null); }
  }

  async function handleSaveVax(payload: VaccinationPayload) {
    const storedToken = getStoredToken();
    if (!storedToken) throw new Error("Not authenticated.");
    if (editingVax) {
      const updated = await apiPut<Vaccination>(
        `/api/v1/records/pets/${petId}/vaccinations/${editingVax.id}`,
        payload as unknown as Record<string, unknown>,
        storedToken
      );
      setVaccinations((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
      setToast("Vaccination updated.");
    } else {
      const created = await apiPost<Vaccination>(
        `/api/v1/records/pets/${petId}/vaccinations`,
        payload as unknown as Record<string, unknown>,
        storedToken
      );
      setVaccinations((prev) => [created, ...prev]);
      setToast("Vaccination logged.");
    }
    setEditingVax(null);
  }

  async function handleDeleteVax(id: string) {
    const storedToken = getStoredToken();
    if (!storedToken) return;
    if (!confirm("Delete this vaccination record?")) return;
    setDeletingId(id);
    try {
      await apiDelete(`/api/v1/records/pets/${petId}/vaccinations/${id}`, storedToken);
      setVaccinations((prev) => prev.filter((v) => v.id !== id));
      setToast("Vaccination record deleted.");
    } catch { setToast("Failed to delete vaccination."); }
    finally { setDeletingId(null); }
  }

  async function handleSaveMed(payload: MedicationPayload) {
    const storedToken = getStoredToken();
    if (!storedToken) throw new Error("Not authenticated.");
    if (editingMed) {
      const updated = await apiPut<Medication>(
        `/api/v1/records/pets/${petId}/medications/${editingMed.id}`,
        payload as unknown as Record<string, unknown>,
        storedToken
      );
      setMedications((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setToast("Medication updated.");
    } else {
      const created = await apiPost<Medication>(
        `/api/v1/records/pets/${petId}/medications`,
        payload as unknown as Record<string, unknown>,
        storedToken
      );
      setMedications((prev) => [created, ...prev]);
      setToast("Medication added.");
    }
    setEditingMed(null);
  }

  async function handleDeleteMed(id: string) {
    const storedToken = getStoredToken();
    if (!storedToken) return;
    if (!confirm("Delete this medication record?")) return;
    setDeletingId(id);
    try {
      await apiDelete(`/api/v1/records/pets/${petId}/medications/${id}`, storedToken);
      setMedications((prev) => prev.filter((m) => m.id !== id));
      setToast("Medication deleted.");
    } catch { setToast("Failed to delete medication."); }
    finally { setDeletingId(null); }
  }

  const timeline: TimelineItem[] = [
    ...healthRecords.map((r) => ({ kind: "record" as const, data: r, date: r.date })),
    ...vaccinations.map((v) => ({ kind: "vaccination" as const, data: v, date: v.administered_date || v.created_at })),
    ...medications.map((m) => ({ kind: "medication" as const, data: m, date: m.start_date || m.created_at })),
  ].sort((a, b) => (a.date < b.date ? 1 : -1));

  const tabs: { id: TabId; label: string; emoji: string; count: number }[] = [
    { id: "timeline", label: "Timeline", emoji: "📅", count: timeline.length },
    { id: "records", label: "Health Records", emoji: "🏥", count: healthRecords.length },
    { id: "vaccinations", label: "Vaccinations", emoji: "💉", count: vaccinations.length },
    { id: "medications", label: "Medications", emoji: "💊", count: medications.length },
  ];

  if (loading) return <RecordsSkeleton />;

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="text-sm font-semibold text-rose-700">{error}</p>
        <button onClick={loadAll} className="mt-4 rounded-xl border border-rose-300 px-4 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition">
          Try again
        </button>
      </div>
    );
  }
  return (
    <>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Link href="/pets" className="hover:text-cyan-600 transition font-medium">My Pets</Link>
            <span>›</span>
            <Link href={`/pets/${petId}`} className="hover:text-cyan-600 transition font-medium">{pet?.name ?? "Pet"}</Link>
            <span>›</span>
            <span className="font-semibold text-slate-700">Health Records</span>
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
            {pet?.name ? `${pet.name}'s Health Records` : "Health Records"}
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">Complete medical history — visits, vaccinations, medications, and attachments.</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button id="add-health-record-btn"
            onClick={() => { setEditingRecord(null); setIsRecordModalOpen(true); setActiveTab("records"); }}
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition">
            + Health Record
          </button>
          <button id="add-vaccination-btn"
            onClick={() => { setEditingVax(null); setIsVaxModalOpen(true); setActiveTab("vaccinations"); }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition">
            💉 Vaccination
          </button>
          <button id="add-medication-btn"
            onClick={() => { setEditingMed(null); setIsMedModalOpen(true); setActiveTab("medications"); }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition">
            💊 Medication
          </button>
        </div>
      </div>

      <div className="mb-6 flex gap-1 rounded-2xl border border-slate-200 bg-slate-50 p-1">
        {tabs.map((tab) => (
          <button key={tab.id} id={`tab-${tab.id}`} onClick={() => setActiveTab(tab.id)}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2.5 text-xs font-semibold transition ${
              activeTab === tab.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}>
            <span>{tab.emoji}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            {tab.count > 0 && (
              <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${activeTab === tab.id ? "bg-cyan-100 text-cyan-700" : "bg-slate-200 text-slate-600"}`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {activeTab === "timeline" && (
        <div>
          {timeline.length === 0 ? (
            <EmptyState icon="📋" title="No records yet"
              subtitle="Start tracking your pet's health by adding a visit, vaccination, or medication."
              action={
                <button onClick={() => { setEditingRecord(null); setIsRecordModalOpen(true); }}
                  className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition">
                  Add First Record
                </button>
              } />
          ) : (
            <div className="relative space-y-0">
              <div className="absolute left-5 top-0 bottom-0 w-px bg-slate-200 pointer-events-none" />
              {timeline.map((item) => {
                if (item.kind === "record") {
                  const { label, emoji, color } = recordTypeLabel(item.data.type);
                  const cardBg = color === "cyan" ? "border-cyan-200 bg-cyan-50/50" : color === "violet" ? "border-violet-200 bg-violet-50/50" : "border-amber-200 bg-amber-50/50";
                  const dotBg = color === "cyan" ? "bg-cyan-500" : color === "violet" ? "bg-violet-500" : "bg-amber-500";
                  const labelColor = color === "cyan" ? "text-cyan-700" : color === "violet" ? "text-violet-700" : "text-amber-700";
                  return (
                    <div key={`rec-${item.data.id}`} className="relative flex gap-4 pb-5">
                      <div className={`relative z-10 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 ${cardBg} text-base`}>
                        {emoji}
                        <span className={`absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white ${dotBg}`} />
                      </div>
                      <div className={`flex-1 rounded-2xl border ${cardBg} p-4`}>
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <span className={`text-[10px] font-bold uppercase tracking-widest ${labelColor}`}>{label}</span>
                            <p className="mt-0.5 text-xs text-slate-500">{fmtDate(item.data.date)}</p>
                          </div>
                          <div className="flex gap-1.5">
                            <button onClick={() => { setEditingRecord(item.data); setIsRecordModalOpen(true); }}
                              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-50 transition">Edit</button>
                            <button onClick={() => handleDeleteRecord(item.data.id)} disabled={deletingId === item.data.id}
                              className="rounded-lg border border-rose-200 bg-rose-50 px-2.5 py-1 text-[10px] font-semibold text-rose-600 hover:bg-rose-100 transition disabled:opacity-50">
                              {deletingId === item.data.id ? "..." : "Delete"}
                            </button>
                          </div>
                        </div>
                        {item.data.weight_kg !== null && item.data.weight_kg !== undefined && (
                          <p className="mt-1.5 text-sm font-semibold text-slate-800">Weight: {item.data.weight_kg} kg</p>
                        )}
                        {item.data.description && <p className="mt-1.5 text-sm text-slate-700 leading-relaxed">{item.data.description}</p>}
                        {item.data.attachment_url && (
                          <a href={getAttachmentUrl(item.data.attachment_url)} target="_blank" rel="noopener noreferrer"
                            className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-cyan-700 hover:underline">
                            📎 View Attachment
                          </a>
                        )}
                      </div>
                    </div>
                  );
                }
                if (item.kind === "vaccination") {
                  const due = isVaxDue(item.data);
                  return (
                    <div key={`vax-${item.data.id}`} className="relative flex gap-4 pb-5">
                      <div className="relative z-10 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-emerald-200 bg-emerald-50 text-base">
                        💉
                        {due && <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-rose-500" />}
                      </div>
                      <div className="flex-1 rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-700">Vaccination</span>
                            <p className="mt-0.5 text-sm font-semibold text-slate-800">{item.data.vaccine_name}</p>
                          </div>
                          <div className="flex gap-1.5">
                            <button onClick={() => { setEditingVax(item.data); setIsVaxModalOpen(true); }}
                              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-50 transition">Edit</button>
                            <button onClick={() => handleDeleteVax(item.data.id)} disabled={deletingId === item.data.id}
                              className="rounded-lg border border-rose-200 bg-rose-50 px-2.5 py-1 text-[10px] font-semibold text-rose-600 hover:bg-rose-100 transition disabled:opacity-50">
                              {deletingId === item.data.id ? "..." : "Delete"}
                            </button>
                          </div>
                        </div>
                        <div className="mt-1.5 flex flex-wrap gap-3 text-xs text-slate-600">
                          {item.data.administered_date && <span>Given: <strong>{fmtDate(item.data.administered_date)}</strong></span>}
                          {item.data.next_due_date && (
                            <span className={due ? "font-semibold text-rose-700" : ""}>
                              Next due: <strong>{fmtDate(item.data.next_due_date)}</strong>{due && " — Overdue"}
                            </span>
                          )}
                        </div>
                        {item.data.notes && <p className="mt-1 text-xs text-slate-500">{item.data.notes}</p>}
                      </div>
                    </div>
                  );
                }
                const active = isMedActive(item.data);
                return (
                  <div key={`med-${item.data.id}`} className="relative flex gap-4 pb-5">
                    <div className="relative z-10 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-purple-200 bg-purple-50 text-base">
                      💊
                      {active && <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-teal-500" />}
                    </div>
                    <div className="flex-1 rounded-2xl border border-purple-200 bg-purple-50/50 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-widest text-purple-700">Medication</span>
                          <p className="mt-0.5 text-sm font-semibold text-slate-800">{item.data.name}</p>
                        </div>
                        <div className="flex gap-1.5">
                          <button onClick={() => { setEditingMed(item.data); setIsMedModalOpen(true); }}
                            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-50 transition">Edit</button>
                          <button onClick={() => handleDeleteMed(item.data.id)} disabled={deletingId === item.data.id}
                            className="rounded-lg border border-rose-200 bg-rose-50 px-2.5 py-1 text-[10px] font-semibold text-rose-600 hover:bg-rose-100 transition disabled:opacity-50">
                            {deletingId === item.data.id ? "..." : "Delete"}
                          </button>
                        </div>
                      </div>
                      <div className="mt-1.5 flex flex-wrap gap-3 text-xs text-slate-600">
                        {item.data.dosage && <span>Dosage: <strong>{item.data.dosage}</strong></span>}
                        {item.data.frequency && <span>Frequency: <strong>{item.data.frequency}</strong></span>}
                        {item.data.start_date && <span>Started: <strong>{fmtDate(item.data.start_date)}</strong></span>}
                        {item.data.end_date && <span>Ends: <strong>{fmtDate(item.data.end_date)}</strong>{!active && " (Done)"}</span>}
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${active ? "bg-teal-100 text-teal-700" : "bg-slate-200 text-slate-500"}`}>
                          {active ? "Active" : "Completed"}
                        </span>
                      </div>
                      {item.data.notes && <p className="mt-1 text-xs text-slate-500">{item.data.notes}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
      {activeTab === "records" && (
        <div className="space-y-3">
          {healthRecords.length === 0 ? (
            <EmptyState icon="🏥" title="No health records yet"
              subtitle="Log vet visits, weight check-ins, and care notes for this pet."
              action={
                <button onClick={() => { setEditingRecord(null); setIsRecordModalOpen(true); }}
                  className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition">
                  Add Health Record
                </button>
              } />
          ) : (
            healthRecords.map((record) => {
              const { label, emoji, color } = recordTypeLabel(record.type);
              const borderL = color === "cyan" ? "border-l-cyan-500" : color === "violet" ? "border-l-violet-500" : "border-l-amber-500";
              const badge = color === "cyan" ? "bg-cyan-100 text-cyan-700" : color === "violet" ? "bg-violet-100 text-violet-700" : "bg-amber-100 text-amber-700";
              return (
                <div key={record.id} className={`rounded-2xl border border-slate-200 border-l-4 ${borderL} bg-white p-5 shadow-xs hover:shadow-sm transition`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{emoji}</span>
                      <div>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${badge}`}>{label}</span>
                        <p className="mt-0.5 text-xs text-slate-500">{fmtDate(record.date)}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => { setEditingRecord(record); setIsRecordModalOpen(true); }}
                        className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition">Edit</button>
                      <button onClick={() => handleDeleteRecord(record.id)} disabled={deletingId === record.id}
                        className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-100 transition disabled:opacity-50">
                        {deletingId === record.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                  {record.weight_kg !== null && record.weight_kg !== undefined && (
                    <p className="mt-3 text-sm font-semibold text-slate-800">Weight: {record.weight_kg} kg</p>
                  )}
                  {record.description && <p className="mt-2 text-sm text-slate-700 leading-relaxed">{record.description}</p>}
                  {record.attachment_url && (
                    <a href={getAttachmentUrl(record.attachment_url)} target="_blank" rel="noopener noreferrer"
                      className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-cyan-700 hover:underline">
                      📎 View Attached Document
                    </a>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === "vaccinations" && (
        <div className="space-y-3">
          {vaccinations.length === 0 ? (
            <EmptyState icon="💉" title="No vaccinations logged"
              subtitle="Keep track of immunizations and set reminders for upcoming boosters."
              action={
                <button onClick={() => { setEditingVax(null); setIsVaxModalOpen(true); }}
                  className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition">
                  Log Vaccination
                </button>
              } />
          ) : (
            vaccinations.map((vax) => {
              const due = isVaxDue(vax);
              return (
                <div key={vax.id} className={`rounded-2xl border border-l-4 p-5 shadow-xs hover:shadow-sm transition ${due ? "border-rose-200 border-l-rose-500 bg-rose-50/30" : "border-slate-200 border-l-emerald-500 bg-white"}`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">💉</span>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">{vax.vaccine_name}</h3>
                        {due && <span className="mt-0.5 inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold text-rose-700">Booster Overdue</span>}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => { setEditingVax(vax); setIsVaxModalOpen(true); }}
                        className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition">Edit</button>
                      <button onClick={() => handleDeleteVax(vax.id)} disabled={deletingId === vax.id}
                        className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-100 transition disabled:opacity-50">
                        {deletingId === vax.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
                    {vax.administered_date && (
                      <div>
                        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Given</span>
                        <p className="font-medium text-slate-800">{fmtDate(vax.administered_date)}</p>
                      </div>
                    )}
                    {vax.next_due_date && (
                      <div>
                        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Next Due</span>
                        <p className={`font-medium ${due ? "text-rose-700" : "text-slate-800"}`}>{fmtDate(vax.next_due_date)}</p>
                      </div>
                    )}
                  </div>
                  {vax.notes && <p className="mt-2 text-xs text-slate-500 leading-relaxed">{vax.notes}</p>}
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === "medications" && (
        <div>
          {medications.length === 0 ? (
            <EmptyState icon="💊" title="No medications recorded"
              subtitle="Track your pet's prescriptions, dosages, and treatment durations."
              action={
                <button onClick={() => { setEditingMed(null); setIsMedModalOpen(true); }}
                  className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition">
                  Add Medication
                </button>
              } />
          ) : (
            <div>
              {medications.filter(isMedActive).length > 0 && (
                <div className="mb-5">
                  <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-teal-700">Active ({medications.filter(isMedActive).length})</h2>
                  <div className="space-y-3">
                    {medications.filter(isMedActive).map((med) => (
                      <div key={med.id} className="rounded-2xl border border-teal-200 border-l-4 border-l-teal-500 bg-teal-50/30 p-5 shadow-xs hover:shadow-sm transition">
                        <MedCard med={med} onEdit={(m) => { setEditingMed(m); setIsMedModalOpen(true); }} onDelete={handleDeleteMed} deletingId={deletingId} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {medications.filter((m) => !isMedActive(m)).length > 0 && (
                <div>
                  <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-500">Completed ({medications.filter((m) => !isMedActive(m)).length})</h2>
                  <div className="space-y-3">
                    {medications.filter((m) => !isMedActive(m)).map((med) => (
                      <div key={med.id} className="rounded-2xl border border-slate-200 border-l-4 border-l-slate-300 bg-white p-5 opacity-75 shadow-xs hover:opacity-100 hover:shadow-sm transition">
                        <MedCard med={med} onEdit={(m) => { setEditingMed(m); setIsMedModalOpen(true); }} onDelete={handleDeleteMed} deletingId={deletingId} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <RecordFormModal
        petId={petId}
        isOpen={isRecordModalOpen}
        onClose={() => { setIsRecordModalOpen(false); setEditingRecord(null); }}
        onSubmit={handleSaveRecord}
        initialData={editingRecord}
        token={token}
      />
      <VaccinationFormModal
        isOpen={isVaxModalOpen}
        onClose={() => { setIsVaxModalOpen(false); setEditingVax(null); }}
        onSubmit={handleSaveVax}
        initialData={editingVax}
      />
      <MedicationFormModal
        isOpen={isMedModalOpen}
        onClose={() => { setIsMedModalOpen(false); setEditingMed(null); }}
        onSubmit={handleSaveMed}
        initialData={editingMed}
      />

      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}
    </>
  );
}

function MedCard({ med, onEdit, onDelete, deletingId }: {
  med: Medication;
  onEdit: (m: Medication) => void;
  onDelete: (id: string) => void;
  deletingId: string | null;
}) {
  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">💊</span>
          <div>
            <h3 className="text-sm font-bold text-slate-900">{med.name}</h3>
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold ${isMedActive(med) ? "bg-teal-100 text-teal-700" : "bg-slate-200 text-slate-500"}`}>
              {isMedActive(med) ? "Active" : "Completed"}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={() => onEdit(med)}
            className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition">Edit</button>
          <button onClick={() => onDelete(med.id)} disabled={deletingId === med.id}
            className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-100 transition disabled:opacity-50">
            {deletingId === med.id ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-sm">
        {med.dosage && <div><span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Dosage</span><p className="font-medium text-slate-800">{med.dosage}</p></div>}
        {med.frequency && <div><span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Frequency</span><p className="font-medium text-slate-800">{med.frequency}</p></div>}
        {med.start_date && <div><span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Started</span><p className="font-medium text-slate-800">{fmtDate(med.start_date)}</p></div>}
        {med.end_date && <div><span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ends</span><p className="font-medium text-slate-800">{fmtDate(med.end_date)}</p></div>}
      </div>
      {med.notes && <p className="mt-2 text-xs text-slate-500 leading-relaxed">{med.notes}</p>}
    </>
  );
}

export default function PetRecordsPage({ params }: PageProps) {
  return (
    <Suspense fallback={<RecordsSkeleton />}>
      <RecordsContent params={params} />
    </Suspense>
  );
}