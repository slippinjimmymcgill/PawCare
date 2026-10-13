import { apiGet } from "@/lib/api";
import type { DashboardOverview, DashboardSummary, Pet } from "@/lib/types";

/**
 * Dashboard aggregation (FR-10).
 *
 * Thin wrappers over the dedicated dashboard endpoints (P1-BE-007). The server
 * assembles the four widgets — weight trend, upcoming reminders, past
 * assessments and record summary — so the dashboard no longer has to compose
 * them from the individual record endpoints client-side.
 */

export async function getDashboardSummary(pet: Pet, token: string): Promise<DashboardSummary> {
  return apiGet<DashboardSummary>(`/api/v1/dashboard/pets/${pet.id}/summary`, token);
}

export async function getDashboardOverview(token: string): Promise<DashboardOverview> {
  return apiGet<DashboardOverview>("/api/v1/dashboard/overview", token);
}
