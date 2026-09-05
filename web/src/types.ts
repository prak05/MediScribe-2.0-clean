export interface Patient {
  id: string;
  name: string;
  dob: string;
  gender: string;
  created_at: string;
}

export interface MedDocument {
  id: string;
  patient_id?: string;
  title: string;
  content: string;
  type: 'pdf' | 'image' | 'note' | 'scribble' | 'voice';
  mode: 'journal' | 'patient';
  created_at: string;
}

export interface Appointment {
  id: string;
  patient_id?: string;
  patient_name?: string;
  title: string;
  type: 'surgery' | 'consultation' | 'followup' | 'other';
  start_time: string;
  end_time?: string;
}

export interface HistoryItem {
  id: string;
  feature: string;
  query: string;
  response: string;
  created_at: string;
}
