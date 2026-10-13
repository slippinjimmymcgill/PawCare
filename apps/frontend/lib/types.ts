export type PetSpecies = "dog" | "cat";
export type PetSex = "male" | "female" | "unknown";

export interface Pet {
  id: string;
  user_id: string;
  name: string;
  species: PetSpecies;
  breed: string | null;
  sex: PetSex;
  date_of_birth: string | null;
  weight_kg: number | null;
  allergies: string | null;
  medical_history: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface PetCreatePayload {
  name: string;
  species: PetSpecies;
  breed?: string | null;
  sex?: PetSex;
  date_of_birth?: string | null;
  weight_kg?: number | null;
  allergies?: string | null;
  medical_history?: string | null;
}

export interface PetUpdatePayload {
  name?: string;
  species?: PetSpecies;
  breed?: string | null;
  sex?: PetSex;
  date_of_birth?: string | null;
  weight_kg?: number | null;
  allergies?: string | null;
  medical_history?: string | null;
}

// Health Record types (visits, weight logs, notes)
export type HealthRecordType = "visit" | "weight_log" | "note";

export interface HealthRecord {
  id: string;
  pet_id: string;
  type: HealthRecordType;
  description: string | null;
  weight_kg: number | null;
  date: string;
  attachment_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface HealthRecordPayload {
  type: HealthRecordType;
  description?: string | null;
  weight_kg?: number | null;
  date: string;
  attachment_url?: string | null;
}

// Vaccination types
export interface Vaccination {
  id: string;
  pet_id: string;
  vaccine_name: string;
  administered_date: string | null;
  next_due_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface VaccinationPayload {
  vaccine_name: string;
  administered_date?: string | null;
  next_due_date?: string | null;
  notes?: string | null;
}

// Medication types
export interface Medication {
  id: string;
  pet_id: string;
  name: string;
  dosage: string | null;
  frequency: string | null;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface MedicationPayload {
  name: string;
  dosage?: string | null;
  frequency?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  notes?: string | null;
}

// Attachment response
export interface AttachmentUploadResponse {
  filename: string;
  original_filename: string;
  url: string;
  mime_type: string;
  size_bytes: number;
}

// Dashboard types (FR-10)
export interface DashboardWeightPoint {
  date: string;
  weight_kg: number;
}

export type DashboardReminderKind = "vaccination" | "medication";
export type DashboardReminderStatus = "overdue" | "due_soon" | "active" | "scheduled";

export interface DashboardReminder {
  id: string;
  kind: DashboardReminderKind;
  title: string;
  due_date: string | null;
  status: DashboardReminderStatus;
}

export interface DashboardAssessment {
  id: string;
  date: string;
  summary: string;
  urgency: string;
}

export interface DashboardRecordSummary {
  total: number;
  visits: number;
  weight_logs: number;
  notes: number;
  last_record_date: string | null;
  active_medications: number;
  upcoming_vaccinations: number;
}

export interface DashboardSummary {
  pet_id: string;
  pet_name: string;
  generated_at: string;
  weight_trend: DashboardWeightPoint[];
  reminders: DashboardReminder[];
  assessments: DashboardAssessment[];
  record_summary: DashboardRecordSummary;
}

export interface DashboardOverview {
  pet_count: number;
  upcoming_reminders: number;
  active_medications: number;
  total_records: number;
}
