export interface TranscriptEntry {
  speaker: string;
  text: string;
}

export interface CallLog {
  id: string;
  callerName: string;
  phoneNumber: string;
  direction: "inbound" | "outbound";
  languages: string[];
  timestamp: string;
  duration: string;
  status: "completed" | "transferred" | "no-answer" | "failed";
  transcript: TranscriptEntry[];
  appointmentId?: string;
}

export interface Appointment {
  id: string;
  callId: string | null;
  patientName: string;
  phoneNumber: string;
  doctorName: string;
  department: string;
  dateTime: string;
  status: "confirmed" | "rescheduled" | "cancelled" | "completed";
  symptoms: string[];
}

export interface DashboardStats {
  totalCalls: number;
  totalAppointments: number;
  completedCalls: number;
  missedCalls: number;
  cancelledAppointments: number;
  callsToday: number;
  appointmentsToday: number;
  transferredCalls: number;
}
