"use client";

import { useState } from "react";
import { apiUpload, getAttachmentUrl } from "@/lib/api";
import type {
  AttachmentUploadResponse,
  HealthRecord,
  HealthRecordPayload,
  HealthRecordType,
} from "@/lib/types";

interface RecordFormModalProps {
  petId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: HealthRecordPayload) => Promise<void>;
  initialData?: HealthRecord | null;
  token: string | null;
}

export function RecordFormModal({
  petId,
  isOpen,
  onClose,
  onSubmit,
  initialData,
  token,
}: RecordFormModalProps) {
  const [type, setType] = useState<HealthRecordType>(initialData?.type || "visit");
  const [date, setDate] = useState(
    initialData?.date || new Date().toISOString().split("T")[0]
  );
  const [description, setDescription] = useState(initialData?.description || "");
  const [weightKg, setWeightKg] = useState<string>(
    initialData?.weight_kg !== null && initialData?.weight_kg !== undefined
      ? String(initialData.weight_kg)
      : ""
  );
  const [attachmentUrl, setAttachmentUrl] = useState<string | null>(
    initialData?.attachment_url || null
  );

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!date) {
      setError("Please select a date for this record.");
      return;
    }

    let parsedWeight: number | null = null;
    if (type === "weight_log") {
      if (!weightKg.trim()) {
        setError("Weight is required for weight log records.");
        return;
      }
      parsedWeight = parseFloat(weightKg);
      if (isNaN(parsedWeight) || parsedWeight <= 0 || parsedWeight > 200) {
        setError("Please enter a valid weight between 0.1 and 200 kg.");
        return;
      }
    } else if (weightKg.trim()) {
      parsedWeight = parseFloat(weightKg);
      if (isNaN(parsedWeight) || parsedWeight <= 0 || parsedWeight > 200) {
        setError("Please enter a valid weight between 0.1 and 200 kg.");
        return;
      }
    }

    try {
      setIsSubmitting(true);
      let finalAttachmentUrl = attachmentUrl;

      // If user selected a new file to upload
      if (selectedFile) {
        setIsUploading(true);
        const formData = new FormData();
        formData.append("file", selectedFile);

        const uploadRes = await apiUpload<AttachmentUploadResponse>(
          `/api/v1/records/pets/${petId}/attachments`,
          formData,
          token
        );
        finalAttachmentUrl = uploadRes.url;
        setIsUploading(false);
      }

      const payload: HealthRecordPayload = {
        type,
        date,
        description: description.trim() || null,
        weight_kg: parsedWeight,
        attachment_url: finalAttachmentUrl,
      };

      await onSubmit(payload);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to save health record.");
      }
    } finally {
      setIsSubmitting(false);
      setIsUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl sm:p-8">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900">
              {initialData ? "Edit Health Record" : "Add Health Record"}
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Log veterinary visits, weight measurements, notes, and attach medical documents.
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
          {/* Record Type Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Record Type <span className="text-rose-500">*</span>
            </label>
            <div className="mt-1.5 grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setType("visit")}
                className={`flex items-center justify-center gap-1.5 rounded-xl border py-2 text-xs font-semibold transition ${
                  type === "visit"
                    ? "border-cyan-600 bg-cyan-50/80 text-cyan-800 ring-1 ring-cyan-600"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>🏥</span> Vet Visit
              </button>
              <button
                type="button"
                onClick={() => setType("weight_log")}
                className={`flex items-center justify-center gap-1.5 rounded-xl border py-2 text-xs font-semibold transition ${
                  type === "weight_log"
                    ? "border-cyan-600 bg-cyan-50/80 text-cyan-800 ring-1 ring-cyan-600"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>⚖️</span> Weight Log
              </button>
              <button
                type="button"
                onClick={() => setType("note")}
                className={`flex items-center justify-center gap-1.5 rounded-xl border py-2 text-xs font-semibold transition ${
                  type === "note"
                    ? "border-cyan-600 bg-cyan-50/80 text-cyan-800 ring-1 ring-cyan-600"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                <span>📝</span> Care Note
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Date <span className="text-rose-500">*</span>
              </label>
              <input
                type="date"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Weight (kg) {type === "weight_log" && <span className="text-rose-500">*</span>}
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="200"
                required={type === "weight_log"}
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                placeholder={type === "weight_log" ? "e.g. 14.2 (Required)" : "e.g. 14.2 (Optional)"}
                className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Details & Observations
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={
                type === "visit"
                  ? "e.g. Annual exam, clear heart and lungs, rabies booster discussed..."
                  : type === "weight_log"
                  ? "e.g. Routine weigh-in, body condition score 5/9..."
                  : "e.g. Mild limping after park visit, monitored for 24h..."
              }
              className="mt-1.5 block w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 shadow-xs focus:border-cyan-500 focus:outline-hidden focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          {/* Attachment Upload Section */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
              Document Attachment (PDF or Image)
            </label>

            {attachmentUrl && !selectedFile && (
              <div className="mt-2 flex items-center justify-between rounded-lg border border-slate-200 bg-white p-2 text-xs">
                <a
                  href={getAttachmentUrl(attachmentUrl)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-cyan-700 hover:underline truncate max-w-[280px]"
                >
                  📎 View Current Attached File
                </a>
                <button
                  type="button"
                  onClick={() => setAttachmentUrl(null)}
                  className="text-xs text-rose-600 hover:text-rose-800 font-semibold ml-2"
                >
                  Remove
                </button>
              </div>
            )}

            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/*"
              onChange={(e) => {
                const file = e.target.files?.[0] || null;
                setSelectedFile(file);
              }}
              className="mt-2 block w-full text-xs text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-cyan-50 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-cyan-700 hover:file:bg-cyan-100"
            />
            {selectedFile && (
              <p className="mt-1 text-[11px] text-teal-700 font-medium">
                Ready to upload: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </p>
            )}
            <p className="mt-1 text-[10px] text-slate-400">
              Supported formats: PDF, JPG, PNG, WEBP (Max 10 MB).
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 hover:from-cyan-700 hover:to-teal-700 transition disabled:opacity-50"
            >
              {isUploading
                ? "Uploading attachment..."
                : isSubmitting
                ? "Saving..."
                : initialData
                ? "Save Changes"
                : "Add Record"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
