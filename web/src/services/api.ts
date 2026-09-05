const API_BASE = 'http://localhost:3000/api';

// Generic API helper
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
};

// Patients
export const getPatients = () => apiCall('/patients');
export const createPatient = (patient: any) => 
  apiCall('/patients', { method: 'POST', body: JSON.stringify(patient) });

// Documents
export const getDocuments = (mode: string, patientId?: string) => 
  apiCall(`/documents?mode=${mode}${patientId ? `&patient_id=${patientId}` : ''}`);
export const createDocument = (doc: any) => 
  apiCall('/documents', { method: 'POST', body: JSON.stringify(doc) });

// Appointments
export const getAppointments = () => apiCall('/appointments');
export const createAppointment = (appointment: any) => 
  apiCall('/appointments', { method: 'POST', body: JSON.stringify(appointment) });

// History
export const getHistory = (feature: string) => apiCall(`/history?feature=${feature}`);
export const createHistory = (history: any) => 
  apiCall('/history', { method: 'POST', body: JSON.stringify(history) });

// RAG Search
export const ragSearch = (query: string, mode: string) => 
  apiCall('/rag-search', { method: 'POST', body: JSON.stringify({ query, mode }) });

// Document Processing
export const processDocument = (content: string, type: string) => 
  apiCall('/process-document', { method: 'POST', body: JSON.stringify({ content, type }) });

// Diagnosis Generation
export const generateDiagnosis = (notes: string, patientId?: string) => 
  apiCall('/generate-diagnosis', { method: 'POST', body: JSON.stringify({ notes, patientId }) });

// File Upload
export const uploadFile = (file: File, mode: string, title: string, patientId?: string) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const base64Content = reader.result as string;
        const response = await fetch(`${API_BASE}/upload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            mode,
            title,
            type: file.type,
            patientId,
            content: base64Content.split(',')[1], // Remove data URL prefix
          }),
        });
        
        if (!response.ok) {
          throw new Error(`Upload failed: ${response.status}`);
        }
        
        resolve(response.json());
      } catch (error) {
        reject(error);
      }
    };
    reader.readAsDataURL(file);
  });
};

// Voice Transcription
export const transcribeAudio = (audioData: string) => 
  apiCall('/transcribe', { method: 'POST', body: JSON.stringify({ audioData }) });
