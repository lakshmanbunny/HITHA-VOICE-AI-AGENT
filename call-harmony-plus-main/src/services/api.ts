/**
 * api.ts — API service layer for the Hitha Hospital dashboard.
 * Connects the frontend to the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── Generic fetch helper ───────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `API error: ${res.status}`);
    }
    return res.json();
}

// ─── Dashboard Stats ────────────────────────────────────────

import type { DashboardStats, CallLog, Appointment } from "@/types/dashboard";

export async function fetchStats(): Promise<DashboardStats> {
    return apiFetch<DashboardStats>("/api/stats");
}

// ─── Call Logs ──────────────────────────────────────────────

export async function fetchCallLogs(): Promise<CallLog[]> {
    return apiFetch<CallLog[]>("/api/calls");
}

export async function fetchCallById(callId: string): Promise<CallLog> {
    return apiFetch<CallLog>(`/api/calls/${callId}`);
}

// ─── Appointments ───────────────────────────────────────────

export async function fetchAppointments(): Promise<Appointment[]> {
    return apiFetch<Appointment[]>("/api/appointments");
}

export async function createAppointment(data: Omit<Appointment, "id" | "callId" | "status">) {
    return apiFetch<Appointment>("/api/appointments", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function updateAppointment(id: string, data: Partial<Appointment>) {
    return apiFetch<Appointment>(`/api/appointments/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

export async function cancelAppointment(id: string) {
    return apiFetch<{ message: string; appointment: Appointment }>(
        `/api/appointments/${id}`,
        { method: "DELETE" }
    );
}

// ─── Doctors ────────────────────────────────────────────────

interface Doctor {
    id: string;
    name: string;
    specialty: string;
    qualification: string;
    experience_years: number;
    language: string[];
}

export async function fetchDoctors(specialty?: string): Promise<Doctor[]> {
    const query = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "";
    return apiFetch<Doctor[]>(`/api/doctors${query}`);
}

export async function fetchDoctorSlots(doctorId: string, date = "tomorrow") {
    return apiFetch<{
        doctor_id: string;
        doctor_name: string;
        date: string;
        available_slots: string[];
        total_available: number;
    }>(`/api/doctors/${doctorId}/slots?date=${encodeURIComponent(date)}`);
}

// ─── Departments ────────────────────────────────────────────

export async function fetchDepartments(): Promise<string[]> {
    return apiFetch<string[]>("/api/departments");
}

// ─── Health Check ───────────────────────────────────────────

export async function healthCheck() {
    return apiFetch<{ status: string; service: string; version: string }>("/api/health");
}
