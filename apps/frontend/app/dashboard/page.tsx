"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, getStoredToken } from "@/lib/api";
import { getDashboardOverview, getDashboardSummary } from "@/lib/dashboard";
import type {
  DashboardOverview,
  DashboardRecordSummary,
  DashboardReminder,
  DashboardSummary,
  DashboardWeightPoint,
  Pet,
} from "@/lib/types";

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.includes("T") ? iso : `${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function fmtKg(value: number): string {
  return Number.isInteger(value) ? `${value}` : value.toFixed(1);
}

function WidgetCard({
  title,
  subtitle,
  action,
  children,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="flex h-full flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-bold tracking-tight text-slate-900">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-5 flex-1">{children}</div>
    </section>
  );
}

function WidgetEmptyState({
  icon,
  title,
  subtitle,
  action,
}: {
  icon: string;
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-6 py-10 text-center">
      <div className="text-3xl opacity-70">{icon}</div>
      <h3 className="mt-3 text-sm font-semibold text-slate-700">{title}</h3>
      <p className="mt-1 max-w-xs text-xs text-slate-400">{subtitle}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

function WeightTrendChart({ points }: { points: DashboardWeightPoint[] }) {
  const width = 600;
  const height = 190;
  const padX = 36;
  const padTop = 24;
  const padBottom = 20;
  const innerWidth = width - padX * 2;
  const innerHeight = height - padTop - padBottom;

  const weights = points.map((p) => p.weight_kg);
  const min = Math.min(...weights);
  const max = Math.max(...weights);
  const span = max - min || 1;

  const coords = points.map((p, index) => {
    const x =
      points.length === 1
        ? width / 2
        : padX + (index / (points.length - 1)) * innerWidth;
    const y = padTop + (1 - (p.weight_kg - min) / span) * innerHeight;
    return { ...p, x, y };
  });

  const linePath = coords
    .map((c, index) => `${index === 0 ? "M" : "L"} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`)
    .join(" ");

  const baseline = height - padBottom;
  const areaPath =
    coords.length > 1
      ? `${linePath} L ${coords[coords.length - 1].x.toFixed(1)} ${baseline} L ${coords[0].x.toFixed(1)} ${baseline} Z`
      : "";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-44 w-full"
      role="img"
      aria-label="Weight over time"
    >
      <defs>
        <linearGradient id="weightArea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
        </linearGradient>
      </defs>

      {[0, 0.5, 1].map((ratio) => (
        <line
          key={ratio}
          x1={padX}
          x2={width - padX}
          y1={padTop + ratio * innerHeight}
          y2={padTop + ratio * innerHeight}
          stroke="#e2e8f0"
          strokeDasharray="4 6"
        />
      ))}

      {areaPath ? <path d={areaPath} fill="url(#weightArea)" /> : null}
      {coords.length > 1 ? (
        <path d={linePath} fill="none" stroke="#0891b2" strokeWidth={2.5} strokeLinecap="round" />
      ) : null}

      {coords.map((c) => (
        <circle key={`${c.date}-${c.x}`} cx={c.x} cy={c.y} r={4} fill="#ffffff" stroke="#0891b2" strokeWidth={2.5} />
      ))}
    </svg>
  );
}

const STATUS_STYLES: Record<DashboardReminder["status"], string> = {
  overdue: "bg-rose-100 text-rose-700",
  due_soon: "bg-amber-100 text-amber-700",
  active: "bg-teal-100 text-teal-700",
  scheduled: "bg-slate-100 text-slate-600",
};

const STATUS_LABELS: Record<DashboardReminder["status"], string> = {
  overdue: "Overdue",
  due_soon: "Due soon",
  active: "Active",
  scheduled: "Scheduled",
};

function ReminderRow({ reminder }: { reminder: DashboardReminder }) {
  const icon = reminder.kind === "vaccination" ? "💉" : "💊";
  return (
    <li className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3.5">
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-base">
          {icon}
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-800">{reminder.title}</p>
          <p className="text-[11px] text-slate-500">
            {reminder.due_date ? `Due ${fmtDate(reminder.due_date)}` : "Ongoing treatment"}
          </p>
        </div>
      </div>
      <span
        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold ${STATUS_STYLES[reminder.status]}`}
      >
        {STATUS_LABELS[reminder.status]}
      </span>
    </li>
  );
}

function RecordSummaryContent({
  summary,
  petId,
}: {
  summary: DashboardRecordSummary;
  petId: string;
}) {
  const rows = [
    { label: "Vet visits", value: summary.visits, icon: "🏥" },
    { label: "Weight logs", value: summary.weight_logs, icon: "⚖️" },
    { label: "Care notes", value: summary.notes, icon: "📝" },
    { label: "Active medications", value: summary.active_medications, icon: "💊" },
    { label: "Upcoming vaccinations", value: summary.upcoming_vaccinations, icon: "💉" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-extrabold tracking-tight text-slate-900">
          {summary.total}
        </span>
        <span className="text-sm text-slate-500">
          {summary.total === 1 ? "record" : "records"} on file
        </span>
      </div>
      <ul className="space-y-1.5">
        {rows.map((row) => (
          <li key={row.label} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="text-base">{row.icon}</span>
              {row.label}
            </span>
            <span className="font-semibold text-slate-800">{row.value}</span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-slate-400">
        Last record: {summary.last_record_date ? fmtDate(summary.last_record_date) : "—"}
      </p>
      <Link
        href={`/pets/${petId}/records`}
        className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-700 hover:text-cyan-800 hover:underline"
      >
        View full history →
      </Link>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-10 w-64 rounded-2xl bg-slate-200" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 rounded-2xl bg-slate-200" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="h-72 rounded-3xl bg-slate-200 lg:col-span-2" />
        <div className="h-72 rounded-3xl bg-slate-200" />
      </div>
    </div>
  );
}

function SignInPrompt() {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-sm">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-cyan-50 text-3xl">
        🔐
      </div>
      <h1 className="mt-4 text-xl font-bold tracking-tight text-slate-900">Sign in to view your dashboard</h1>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
        Your health-monitoring overview shows weight trends, reminders, and assessments for each pet.
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
  );
}

function NoPetsPrompt() {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-xs">
      <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-slate-50 text-4xl shadow-inner">
        🐶🐱
      </div>
      <h1 className="mt-4 text-xl font-bold tracking-tight text-slate-900">No pets to summarize yet</h1>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
        Add a pet profile and their health records to populate the dashboard widgets.
      </p>
      <Link
        href="/pets"
        className="mt-6 inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-cyan-700 transition"
      >
        <span>+</span> Go to My Pets
      </Link>
    </div>
  );
}

export default function DashboardPage() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [pets, setPets] = useState<Pet[]>([]);
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loadingPets, setLoadingPets] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const selectedPet = useMemo(
    () => pets.find((p) => p.id === selectedPetId) ?? null,
    [pets, selectedPetId],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadPets() {
      await Promise.resolve();
      const token = getStoredToken();
      if (!token) {
        if (!cancelled) {
          setAuthed(false);
          setLoadingPets(false);
        }
        return;
      }

      if (!cancelled) {
        setAuthed(true);
        setLoadingPets(true);
        setError(null);
      }

      try {
        const data = await apiGet<Pet[]>("/api/v1/pets", token);
        if (cancelled) return;
        setPets(data);
        setSelectedPetId(data.length > 0 ? data[0].id : null);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load pets.");
        }
      } finally {
        if (!cancelled) setLoadingPets(false);
      }
    }

    loadPets();

    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  useEffect(() => {
    let cancelled = false;

    async function loadSummary() {
      await Promise.resolve();
      if (cancelled) return;

      if (!authed || !selectedPet) {
        setSummary(null);
        return;
      }

      const token = getStoredToken();
      if (!token) return;

      setLoadingSummary(true);
      setError(null);

      try {
        const data = await getDashboardSummary(selectedPet, token);
        if (!cancelled) setSummary(data);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load the dashboard.");
        }
      } finally {
        if (!cancelled) setLoadingSummary(false);
      }
    }

    loadSummary();

    return () => {
      cancelled = true;
    };
  }, [authed, selectedPet]);

  useEffect(() => {
    let cancelled = false;

    async function loadOverview() {
      await Promise.resolve();
      if (cancelled || !authed) {
        if (!authed) setOverview(null);
        return;
      }

      const token = getStoredToken();
      if (!token) return;

      try {
        const data = await getDashboardOverview(token);
        if (!cancelled) setOverview(data);
      } catch {
        if (!cancelled) setOverview(null);
      }
    }

    loadOverview();

    return () => {
      cancelled = true;
    };
  }, [authed, reloadKey]);

  const reload = useCallback(() => {
    setError(null);
    setReloadKey((key) => key + 1);
  }, []);

  if (authed === false) return <SignInPrompt />;
  if (loadingPets) return <DashboardSkeleton />;

  if (error && pets.length === 0) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-10 text-center shadow-sm">
        <div className="text-3xl">⚠️</div>
        <h1 className="mt-3 text-lg font-bold text-rose-900">Could not load your dashboard</h1>
        <p className="mt-1 text-sm text-rose-700">{error}</p>
        <button
          type="button"
          onClick={reload}
          className="mt-5 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-700 transition"
        >
          Try again
        </button>
      </div>
    );
  }

  if (pets.length === 0) return <NoPetsPrompt />;

  const recordSummary = summary?.record_summary;
  const statCards = [
    { label: "Pets", value: `${overview?.pet_count ?? pets.length}` },
    {
      label: "Upcoming reminders",
      value: `${overview?.upcoming_reminders ?? summary?.reminders.length ?? 0}`,
    },
    {
      label: "Active medications",
      value: `${overview?.active_medications ?? recordSummary?.active_medications ?? 0}`,
    },
    { label: "Health records", value: `${overview?.total_records ?? recordSummary?.total ?? 0}` },
  ];

  return (
    <div id="dashboard-page" className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-600">Overview</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">
            Weight trends, reminders, assessments, and record summaries for your pets.
          </p>
        </div>

        {pets.length > 1 ? (
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-500">
            Pet
            <select
              id="pet-selector"
              value={selectedPetId ?? ""}
              onChange={(event) => setSelectedPetId(event.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 shadow-xs focus:border-cyan-500 focus:outline-none"
            >
              {pets.map((pet) => (
                <option key={pet.id} value={pet.id}>
                  {pet.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      {error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map((card) => (
          <div key={card.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="text-sm text-slate-500">{card.label}</div>
            <div className="mt-3 text-3xl font-bold text-slate-900">{card.value}</div>
          </div>
        ))}
      </div>

      {loadingSummary || !summary || !recordSummary ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="h-80 rounded-3xl bg-slate-200 animate-pulse lg:col-span-2" />
          <div className="h-80 rounded-3xl bg-slate-200 animate-pulse" />
        </div>
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <WidgetCard
                title="Weight trend"
                subtitle={
                  selectedPet ? `${selectedPet.name}'s weight over time` : "Weight over time"
                }
                action={
                  summary.weight_trend.length > 0 ? (
                    <span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-700">
                      {fmtKg(summary.weight_trend[summary.weight_trend.length - 1].weight_kg)} kg
                    </span>
                  ) : null
                }
              >
                {summary.weight_trend.length === 0 ? (
                  <WidgetEmptyState
                    icon="⚖️"
                    title="No weight recorded yet"
                    subtitle="Log a weight check-in in health records to start tracking a trend."
                    action={
                      selectedPet ? (
                        <Link
                          href={`/pets/${selectedPet.id}/records`}
                          className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:from-cyan-700 hover:to-teal-700 transition"
                        >
                          Add a weight log
                        </Link>
                      ) : null
                    }
                  />
                ) : (
                  <div>
                    <WeightTrendChart points={summary.weight_trend} />
                    <div className="mt-1 flex justify-between px-1 text-[11px] text-slate-400">
                      <span>{fmtDate(summary.weight_trend[0].date)}</span>
                      {summary.weight_trend.length > 1 ? (
                        <span>
                          {fmtDate(summary.weight_trend[summary.weight_trend.length - 1].date)}
                        </span>
                      ) : (
                        <span>Single reading</span>
                      )}
                    </div>
                  </div>
                )}
              </WidgetCard>
            </div>

            <WidgetCard
              title="Upcoming reminders"
              subtitle="Vaccinations and treatments needing attention"
            >
              {summary.reminders.length === 0 ? (
                <WidgetEmptyState
                  icon="🔔"
                  title="Nothing scheduled"
                  subtitle="Vaccination due dates and active medications will appear here."
                />
              ) : (
                <ul className="space-y-2.5">
                  {summary.reminders.slice(0, 6).map((reminder) => (
                    <ReminderRow key={reminder.id} reminder={reminder} />
                  ))}
                </ul>
              )}
            </WidgetCard>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <WidgetCard
                title="Past assessments"
                subtitle="Symptom checks and their triage outcomes"
                action={
                  selectedPet ? (
                    <Link
                      href={`/pets/${selectedPet.id}/assess`}
                      className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                    >
                      New assessment
                    </Link>
                  ) : null
                }
              >
                {summary.assessments.length === 0 ? (
                  <WidgetEmptyState
                    icon="🩺"
                    title="No assessments yet"
                    subtitle="Run a symptom check to see its result and urgency here."
                    action={
                      selectedPet ? (
                        <Link
                          href={`/pets/${selectedPet.id}/assess`}
                          className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:from-cyan-700 hover:to-teal-700 transition"
                        >
                          Start an assessment
                        </Link>
                      ) : null
                    }
                  />
                ) : (
                  <ul className="space-y-3">
                    {summary.assessments.map((assessment) => (
                      <li
                        key={assessment.id}
                        className="rounded-2xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-500">{fmtDate(assessment.date)}</span>
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-600">
                            {assessment.urgency}
                          </span>
                        </div>
                        <p className="mt-1.5 text-sm text-slate-700">{assessment.summary}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </WidgetCard>
            </div>

            <WidgetCard
              title="Record summary"
              subtitle="What's on file for this pet"
              action={
                selectedPet ? (
                  <Link
                    href={`/pets/${selectedPet.id}/records`}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                  >
                    Manage
                  </Link>
                ) : null
              }
            >
              {recordSummary.total === 0 &&
              recordSummary.active_medications === 0 &&
              recordSummary.upcoming_vaccinations === 0 ? (
                <WidgetEmptyState
                  icon="📋"
                  title="No records yet"
                  subtitle="Add a visit, weight log, or note to build this pet's history."
                  action={
                    selectedPet ? (
                      <Link
                        href={`/pets/${selectedPet.id}/records`}
                        className="rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:from-cyan-700 hover:to-teal-700 transition"
                      >
                        Add a record
                      </Link>
                    ) : null
                  }
                />
              ) : selectedPet ? (
                <RecordSummaryContent summary={recordSummary} petId={selectedPet.id} />
              ) : null}
            </WidgetCard>
          </div>
        </>
      )}
    </div>
  );
}
