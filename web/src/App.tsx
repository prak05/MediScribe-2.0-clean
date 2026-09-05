import React, { useState, useEffect, useRef } from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  Users, 
  Calendar as CalendarIcon, 
  Search, 
  Plus, 
  Mic, 
  PenTool, 
  FileText, 
  ChevronRight, 
  X, 
  Maximize2, 
  Minimize2,
  Upload,
  History,
  Send,
  MoreVertical,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  Command,
  Settings,
  Bell,
  Sun,
  Moon,
  Filter,
  Bookmark,
  Share2,
  Download,
  Trash2,
  Heart,
  Activity,
  Stethoscope,
  User
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Stage, Layer, Line } from 'react-konva';
import Markdown from 'react-markdown';
import { 
  LineChart, 
  Line as ReLine, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { Patient, MedDocument, Appointment, HistoryItem } from './types';
import * as api from './services/api';
import { generateRAGResponse, generateDiagnosis, transcribeAudio } from './services/geminiService';

// --- Types & Constants ---

type Mode = 'journal' | 'patient';

// --- Components ---

const ThemeToggle = ({ isDark, setIsDark }: { isDark: boolean, setIsDark: (d: boolean) => void }) => {
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <button 
      onClick={() => setIsDark(!isDark)}
      className="p-2.5 hover:bg-black/[0.05] dark:hover:bg-white/[0.05] rounded-full transition-colors text-apple-secondary-text"
    >
      {isDark ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
};

const ModeToggle = ({ mode, setMode }: { mode: Mode, setMode: (m: Mode) => void }) => (
  <div className="segmented-control">
    <button 
      onClick={() => setMode('journal')}
      className={`segmented-item ${mode === 'journal' ? 'segmented-item-active' : 'segmented-item-inactive'}`}
    >
      Journal
    </button>
    <button 
      onClick={() => setMode('patient')}
      className={`segmented-item ${mode === 'patient' ? 'segmented-item-active' : 'segmented-item-inactive'}`}
    >
      Patient
    </button>
  </div>
);

const FeatureCard = ({ 
  title, 
  icon: Icon, 
  description, 
  onClick, 
  color = "bg-white",
  accentColor = "text-apple-blue",
  size = "normal"
}: { 
  title: string, 
  icon: any, 
  description: string, 
  onClick: () => void,
  color?: string,
  accentColor?: string,
  size?: 'normal' | 'large' | 'wide'
}) => {
  const sizeClasses = {
    normal: "col-span-1 row-span-1",
    large: "col-span-1 sm:col-span-2 row-span-2",
    wide: "col-span-1 sm:col-span-2 row-span-1"
  };

  return (
    <motion.div 
      layoutId={`card-${title}`}
      whileHover={{ scale: 1.01, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`journal-card cursor-pointer group flex flex-col ${sizeClasses[size]} ${color}`}
    >
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-all duration-300 ${accentColor} bg-black/[0.03] group-hover:bg-apple-blue group-hover:text-white`}>
        <Icon size={24} />
      </div>
      <h3 className="text-xl font-bold mb-2 font-sans tracking-tight">{title}</h3>
      <p className="text-sm text-apple-secondary-text leading-relaxed flex-1">{description}</p>
      {size !== 'normal' && (
        <div className="mt-4 pt-4 border-t border-black/[0.03] flex items-center text-apple-blue font-semibold text-sm">
          Explore Feature <ArrowRight size={14} className="ml-2 group-hover:translate-x-1 transition-transform" />
        </div>
      )}
    </motion.div>
  );
};

const FullscreenModal = ({ 
  isOpen, 
  onClose, 
  title, 
  children,
  icon: Icon,
  id
}: { 
  isOpen: boolean, 
  onClose: () => void, 
  title: string, 
  children: React.ReactNode,
  icon: any,
  id: string
}) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-apple-bg/95 backdrop-blur-2xl"
      >
        <motion.div 
          layoutId={`card-${id}`}
          className="w-full h-full flex flex-col animate-apple-slide-up"
        >
          <header className="glass-header px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={onClose} className="p-2 hover:bg-black/[0.05] rounded-full transition-colors">
                <ChevronRight size={24} className="rotate-180" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-apple-blue/10 text-apple-blue flex items-center justify-center">
                  <Icon size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold tracking-tight">{title}</h2>
                  <p className="text-[10px] text-apple-secondary-text font-bold uppercase tracking-widest">MediScribe Workspace</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 hover:bg-black/[0.05] rounded-full text-apple-secondary-text"><Share2 size={20} /></button>
              <button onClick={onClose} className="p-2 hover:bg-red-50 hover:text-red-500 rounded-full text-apple-secondary-text">
                <X size={20} />
              </button>
            </div>
          </header>
          <main className="flex-1 overflow-y-auto p-6 md:p-12">
            <div className="max-w-5xl mx-auto w-full h-full">
              {children}
            </div>
          </main>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);

// --- Feature Content Components ---

const DrDrishti = ({ mode }: { mode: string }) => {
  const [query, setQuery] = useState('');
  const [chat, setChat] = useState<{role: string, text: string}[]>([]);
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<MedDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<MedDocument | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
  }, [mode]);

  const loadDocuments = async () => {
    try {
      const docs = await api.getDocuments(mode);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await api.uploadFile(file, mode, file.name);
      await loadDocuments();
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleAsk = async () => {
    if (!query) return;
    setLoading(true);
    setChat(prev => [...prev, { role: 'user', text: query }]);
    
    try {
      const response = await api.ragSearch(query, mode);
      setChat(prev => [...prev, { role: 'ai', text: response.answer }]);
    } catch (error) {
      setChat(prev => [...prev, { role: 'ai', text: 'Search failed. Please try again.' }]);
    }
    
    setLoading(false);
    setQuery('');
  };

  const processDocument = async (doc: MedDocument) => {
    try {
      const response = await api.processDocument(doc.content, doc.type);
      // Update document with processed content
      setSelectedDoc({ ...doc, content: response.processedContent });
    } catch (error) {
      console.error('Processing failed:', error);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
      <div className="lg:col-span-2 space-y-8">
        <div className="journal-card bg-white p-8 md:p-12">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-apple-blue/10 text-apple-blue rounded-xl flex items-center justify-center">
                <FileText size={20} />
              </div>
              <h3 className="text-xl font-bold">Document Viewer</h3>
            </div>
            <div className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleUpload}
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png,.txt"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-apple-blue text-white rounded-xl text-sm font-bold shadow-md"
              >
                Upload Document
              </button>
              {selectedDoc && (
                <button
                  onClick={() => processDocument(selectedDoc)}
                  className="px-4 py-2 bg-apple-purple text-white rounded-xl text-sm font-bold shadow-md"
                >
                  Process Text
                </button>
              )}
            </div>
          </div>
          
          {selectedDoc ? (
            <div className="prose prose-slate max-w-none">
              <h1 className="font-serif italic text-2xl mb-4">{selectedDoc.title}</h1>
              <div className="bg-apple-bg rounded-xl p-6">
                <pre className="whitespace-pre-wrap text-sm text-apple-secondary-text">
                  {selectedDoc.content}
                </pre>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <h4 className="text-lg font-semibold">Uploaded Documents</h4>
              {documents.length === 0 ? (
                <div className="text-center py-12 text-apple-secondary-text">
                  <FileText size={48} className="mx-auto mb-4 opacity-50" />
                  <p>No documents uploaded yet</p>
                </div>
              ) : (
                documents.map(doc => (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc)}
                    className="p-4 bg-apple-bg rounded-xl cursor-pointer hover:bg-apple-bg/70 transition-colors"
                  >
                    <div className="font-semibold">{doc.title}</div>
                    <div className="text-xs text-apple-secondary-text">{doc.type} • {new Date(doc.created_at).toLocaleDateString()}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
      <div className="flex flex-col gap-6">
        <div className="journal-card bg-white p-6 flex-1 flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <Sparkles size={18} className="text-apple-purple" />
            <h4 className="font-bold">AI Insights</h4>
          </div>
          <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2">
            {chat.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-4 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-apple-blue text-white' : 'bg-apple-bg text-apple-text'}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {loading && <div className="text-xs text-apple-secondary-text animate-pulse">Analyzing document...</div>}
          </div>
          <div className="relative">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              placeholder="Ask about this case..."
              className="w-full bg-apple-bg border-none rounded-xl py-3 pl-4 pr-10 text-sm focus:ring-2 focus:ring-apple-blue transition-all"
            />
            <button onClick={handleAsk} className="absolute right-2 top-1/2 -translate-y-1/2 text-apple-blue">
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const DrDoodle = ({ mode }: { mode: string }) => {
  const [lines, setLines] = useState<any[]>([]);
  const isDrawing = useRef(false);

  const handleMouseDown = (e: any) => {
    isDrawing.current = true;
    const pos = e.target.getStage().getPointerPosition();
    setLines([...lines, { points: [pos.x, pos.y] }]);
  };

  const handleMouseMove = (e: any) => {
    if (!isDrawing.current) return;
    const stage = e.target.getStage();
    const point = stage.getPointerPosition();
    let lastLine = lines[lines.length - 1];
    lastLine.points = lastLine.points.concat([point.x, point.y]);
    lines.splice(lines.length - 1, 1, lastLine);
    setLines(lines.concat());
  };

  const handleMouseUp = () => {
    isDrawing.current = false;
  };

  const exportCanvas = async () => {
    try {
      // Create a simple representation of the drawing
      const canvasData = JSON.stringify(lines);
      await api.createDocument({
        id: crypto.randomUUID(),
        title: `Drawing - ${new Date().toLocaleString()}`,
        content: canvasData,
        type: 'scribble',
        mode
      });
      alert('Drawing saved successfully!');
    } catch (error) {
      console.error('Save failed:', error);
      alert('Failed to save drawing.');
    }
  };

  const clearCanvas = () => {
    setLines([]);
  };

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white dark:bg-dark-card rounded-xl text-sm font-bold shadow-sm border border-black/[0.03] dark:border-white/[0.05]">Pen</button>
          <button className="px-4 py-2 hover:bg-white dark:hover:bg-white/[0.05] rounded-xl text-sm font-bold text-apple-secondary-text transition-colors">Eraser</button>
          <button onClick={clearCanvas} className="px-4 py-2 text-red-500 text-sm font-bold hover:bg-red-50 dark:hover:bg-red-500/10 rounded-xl transition-colors">Clear</button>
        </div>
        <div className="flex gap-2">
          <button onClick={exportCanvas} className="px-6 py-2 bg-apple-blue text-white rounded-xl text-sm font-bold shadow-lg flex items-center gap-2">
            <Download size={16} /> Save Drawing
          </button>
          <button className="px-6 py-2 bg-apple-purple text-white rounded-xl text-sm font-bold shadow-lg flex items-center gap-2">
            <Sparkles size={16} /> Analyze Sketch
          </button>
        </div>
      </div>
      <div className="flex-1 bg-white dark:bg-dark-card rounded-[2rem] border border-black/[0.03] dark:border-white/[0.05] shadow-inner overflow-hidden cursor-crosshair">
        <Stage
          width={1000}
          height={600}
          onMouseDown={handleMouseDown}
          onMousemove={handleMouseMove}
          onMouseup={handleMouseUp}
        >
          <Layer>
            {lines.map((line, i) => (
              <Line
                key={i}
                points={line.points}
                stroke="#007AFF"
                strokeWidth={3}
                tension={0.5}
                lineCap="round"
                lineJoin="round"
              />
            ))}
          </Layer>
        </Stage>
      </div>
    </div>
  );
};

const DhvaniSanchar = ({ mode }: { mode: string }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);

  const toggleRecording = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        const chunks: Blob[] = [];

        recorder.ondataavailable = (e) => {
          chunks.push(e.data);
        };

        recorder.onstop = async () => {
          const audioBlob = new Blob(chunks, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.onloadend = async () => {
            const base64Audio = reader.result as string;
            try {
              const response = await api.transcribeAudio(base64Audio);
              setTranscript(prev => [...prev, response.transcription]);
              // Save as document
              await api.createDocument({
                id: crypto.randomUUID(),
                title: `Voice Note - ${new Date().toLocaleString()}`,
                content: response.transcription,
                type: 'voice',
                mode
              });
            } catch (error) {
              console.error('Transcription failed:', error);
              setTranscript(prev => [...prev, 'Transcription failed. Please try again.']);
            }
          };
          reader.readAsDataURL(audioBlob);
        };

        setMediaRecorder(recorder);
        setAudioChunks(chunks);
        recorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Failed to start recording:', error);
        alert('Failed to access microphone. Please check permissions.');
      }
    } else {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
      setIsRecording(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-8">
      <div className="flex flex-col items-center justify-center py-12 bg-apple-bg/50 dark:bg-white/[0.02] rounded-[2.5rem] border border-black/[0.02] dark:border-white/[0.05]">
        <motion.button 
          animate={isRecording ? { scale: [1, 1.1, 1] } : {}}
          transition={{ repeat: Infinity, duration: 2 }}
          onClick={toggleRecording}
          className={`w-24 h-24 rounded-full flex items-center justify-center shadow-2xl transition-colors ${isRecording ? 'bg-red-500 text-white' : 'bg-apple-blue text-white'}`}
        >
          {isRecording ? <X size={40} /> : <Mic size={40} />}
        </motion.button>
        <div className="mt-6 text-center">
          <h3 className="text-xl font-bold">{isRecording ? 'Recording Rounds...' : 'Start Ambient Recording'}</h3>
          <p className="text-apple-secondary-text text-sm mt-1">{isRecording ? 'Listening for clinical dialogue' : 'Tap to begin real-time transcription'}</p>
        </div>
      </div>
      <div className="flex-1 bg-white dark:bg-dark-card rounded-[2rem] p-8 border border-black/[0.02] dark:border-white/[0.05] overflow-y-auto">
        <h4 className="text-xs font-bold text-apple-secondary-text uppercase tracking-widest mb-6">Live Transcript</h4>
        <div className="space-y-4">
          {transcript.map((line, i) => (
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} key={i} className="p-4 bg-apple-bg dark:bg-white/[0.05] rounded-xl text-sm leading-relaxed">
              {line}
            </motion.div>
          ))}
          {transcript.length === 0 && !isRecording && (
            <div className="text-center py-12 text-apple-secondary-text italic text-sm">No active transcription</div>
          )}
          {isRecording && (
            <div className="flex items-center gap-2 text-apple-blue text-xs font-bold animate-pulse">
              <div className="w-1.5 h-1.5 bg-apple-blue rounded-full"></div>
              Processing audio...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const SimpleText = ({ mode }: { mode: string }) => {
  const [text, setText] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const generateContent = async () => {
    if (!aiPrompt) return;
    setIsGenerating(true);
    
    try {
      const response = await api.ragSearch(aiPrompt, mode);
      setText(response.answer);
    } catch (error) {
      console.error('Generation failed:', error);
      setText('Failed to generate content. Please try again.');
    }
    
    setIsGenerating(false);
    setAiPrompt('');
  };

  const saveNote = async () => {
    if (!text.trim()) return;
    
    try {
      await api.createDocument({
        id: crypto.randomUUID(),
        title: `Text Note - ${new Date().toLocaleString()}`,
        content: text,
        type: 'note',
        mode
      });
      alert('Note saved successfully!');
    } catch (error) {
      console.error('Save failed:', error);
      alert('Failed to save note.');
    }
  };

  const exportAsPDF = () => {
    // Simple text export for MVP
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `note-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold">Clinical Note Editor</h3>
        <div className="flex gap-2">
          <button onClick={saveNote} className="px-4 py-2 bg-apple-blue text-white rounded-xl text-sm font-bold shadow-md">Save Note</button>
          <button onClick={exportAsPDF} className="px-4 py-2 bg-white dark:bg-dark-card rounded-xl text-sm font-bold border border-black/[0.03] dark:border-white/[0.05]">Export</button>
        </div>
      </div>
      <div className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            placeholder="Ask AI to generate content..."
            className="flex-1 bg-apple-bg rounded-xl px-4 py-2 text-sm outline-none"
          />
          <button
            onClick={generateContent}
            disabled={isGenerating}
            className="px-4 py-2 bg-apple-purple text-white rounded-xl text-sm font-bold disabled:opacity-50"
          >
            {isGenerating ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </div>
      <textarea 
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Start typing your clinical notes here..."
        className="flex-1 bg-white dark:bg-dark-card rounded-[2rem] p-10 border border-black/[0.02] dark:border-white/[0.05] shadow-inner focus:ring-2 focus:ring-apple-blue outline-none resize-none text-lg leading-relaxed"
      />
    </div>
  );
};

const ReportReviewer = () => (
  <div className="h-full flex flex-col gap-8">
    <div className="grid grid-cols-2 gap-8 flex-1">
      <div className="bg-white dark:bg-dark-card rounded-[2rem] p-8 border border-black/[0.02] dark:border-white/[0.05] shadow-sm">
        <h4 className="text-xs font-bold text-apple-secondary-text uppercase tracking-widest mb-6">Diagnostic Report</h4>
        <div className="space-y-4 text-sm text-apple-secondary-text leading-relaxed">
          <p className="font-bold text-apple-text">Lab Results - Feb 24, 2026</p>
          <p>WBC: 7.2 x10^3/uL (Normal)</p>
          <p>RBC: 4.8 x10^6/uL (Normal)</p>
          <p>Hemoglobin: 14.2 g/dL (Normal)</p>
          <p>Platelets: 210 x10^3/uL (Normal)</p>
          <div className="pt-4 border-t border-black/[0.03] dark:border-white/[0.05]">
            <p className="font-bold text-apple-text">Interpretation</p>
            <p>All hematological parameters are within standard reference ranges. No evidence of infection or anemia.</p>
          </div>
        </div>
      </div>
      <div className="bg-white dark:bg-dark-card rounded-[2rem] p-8 border border-black/[0.02] dark:border-white/[0.05] shadow-sm flex flex-col">
        <h4 className="text-xs font-bold text-apple-secondary-text uppercase tracking-widest mb-6">Reviewer Notes</h4>
        <textarea className="flex-1 bg-apple-bg dark:bg-white/[0.02] rounded-xl p-4 text-sm outline-none resize-none" placeholder="Add your clinical observations..." />
      </div>
    </div>
  </div>
);

const DiagnosisGen = () => {
  const [notes, setNotes] = useState('');
  const [diagnosis, setDiagnosis] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<string>('');
  const [patients, setPatients] = useState<Patient[]>([]);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const patientList = await api.getPatients();
      setPatients(patientList);
    } catch (error) {
      console.error('Failed to load patients:', error);
    }
  };

  const generateDiagnosis = async () => {
    if (!notes.trim()) return;
    setIsGenerating(true);
    
    try {
      const response = await api.generateDiagnosis(notes, selectedPatient);
      setDiagnosis(response.diagnosis);
    } catch (error) {
      console.error('Diagnosis generation failed:', error);
      alert('Failed to generate diagnosis. Please try again.');
    }
    
    setIsGenerating(false);
  };

  const saveDiagnosis = async () => {
    if (!diagnosis) return;
    
    try {
      await api.createDocument({
        id: crypto.randomUUID(),
        patient_id: selectedPatient,
        title: `Diagnosis - ${new Date().toLocaleString()}`,
        content: JSON.stringify(diagnosis, null, 2),
        type: 'note',
        mode: 'patient'
      });
      alert('Diagnosis saved successfully!');
    } catch (error) {
      console.error('Save failed:', error);
      alert('Failed to save diagnosis.');
    }
  };

  return (
    <div className="h-full flex flex-col gap-8">
      <div className="bg-apple-purple/5 dark:bg-apple-purple/10 rounded-[2.5rem] p-10 border border-apple-purple/10">
        <div className="flex items-center gap-4 mb-8">
          <div className="w-14 h-14 bg-apple-purple text-white rounded-2xl flex items-center justify-center shadow-lg">
            <Sparkles size={28} />
          </div>
          <div>
            <h3 className="text-2xl font-bold">Diagnosis Generator</h3>
            <p className="text-apple-secondary-text">Evidence-based treatment planning</p>
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="p-6 bg-white dark:bg-dark-card rounded-2xl shadow-sm border border-black/[0.02] dark:border-white/[0.05]">
            <div className="mb-4">
              <label className="block text-sm font-bold mb-2">Select Patient</label>
              <select 
                value={selectedPatient}
                onChange={(e) => setSelectedPatient(e.target.value)}
                className="w-full p-3 bg-apple-bg rounded-xl border-none outline-none"
              >
                <option value="">Choose a patient...</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-bold mb-2">Clinical Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Enter clinical observations and notes..."
                className="w-full h-32 p-3 bg-apple-bg rounded-xl border-none outline-none resize-none"
              />
            </div>
            <button
              onClick={generateDiagnosis}
              disabled={isGenerating || !notes.trim()}
              className="w-full py-3 bg-apple-purple text-white rounded-xl font-bold disabled:opacity-50"
            >
              {isGenerating ? 'Generating...' : 'Generate Diagnosis'}
            </button>
          </div>
          
          {diagnosis && (
            <div className="p-6 bg-white dark:bg-dark-card rounded-2xl shadow-sm border border-black/[0.02] dark:border-white/[0.05]">
              <h5 className="font-bold mb-2">Generated Diagnosis</h5>
              <div className="space-y-4 text-sm">
                <div>
                  <strong>Diagnosis:</strong> {diagnosis.diagnosis}
                </div>
                <div>
                  <strong>Treatment Plan:</strong> {diagnosis.plan}
                </div>
                <div>
                  <strong>Medications:</strong>
                  <ul className="list-disc pl-5 mt-1">
                    {diagnosis.medications?.map((med: string, i: number) => (
                      <li key={i}>{med}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <strong>Confidence:</strong> {Math.round((diagnosis.confidence_score || 0) * 100)}%
                </div>
              </div>
              <button
                onClick={saveDiagnosis}
                className="mt-4 w-full py-2 bg-apple-blue text-white rounded-xl font-bold"
              >
                Save Diagnosis
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const PatientModeContent = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showAddPatient, setShowAddPatient] = useState(false);
  const [newPatient, setNewPatient] = useState({ name: '', dob: '', gender: 'Male' });

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const patientList = await api.getPatients();
      setPatients(patientList);
    } catch (error) {
      console.error('Failed to load patients:', error);
    }
  };

  const addPatient = async () => {
    if (!newPatient.name || !newPatient.dob) return;
    
    try {
      const patient = {
        id: crypto.randomUUID(),
        ...newPatient
      };
      await api.createPatient(patient);
      await loadPatients();
      setNewPatient({ name: '', dob: '', gender: 'Male' });
      setShowAddPatient(false);
    } catch (error) {
      console.error('Failed to add patient:', error);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-full">
      <div className="lg:col-span-1 space-y-4">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-apple-secondary-text" />
            <input 
              type="text" 
              placeholder="Search patients..."
              className="w-full bg-white border-none rounded-xl py-3 pl-11 pr-4 text-sm shadow-sm focus:ring-2 focus:ring-apple-blue"
            />
          </div>
          <button
            onClick={() => setShowAddPatient(true)}
            className="ml-2 p-3 bg-apple-blue text-white rounded-xl shadow-sm"
          >
            <Plus size={16} />
          </button>
        </div>
        
        {showAddPatient && (
          <div className="p-4 bg-apple-blue/10 rounded-xl border border-apple-blue/20">
            <h4 className="font-bold mb-3">Add New Patient</h4>
            <div className="space-y-2">
              <input
                type="text"
                placeholder="Name"
                value={newPatient.name}
                onChange={(e) => setNewPatient({...newPatient, name: e.target.value})}
                className="w-full p-2 bg-white rounded-lg text-sm"
              />
              <input
                type="date"
                value={newPatient.dob}
                onChange={(e) => setNewPatient({...newPatient, dob: e.target.value})}
                className="w-full p-2 bg-white rounded-lg text-sm"
              />
              <select
                value={newPatient.gender}
                onChange={(e) => setNewPatient({...newPatient, gender: e.target.value})}
                className="w-full p-2 bg-white rounded-lg text-sm"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
              <div className="flex gap-2">
                <button
                  onClick={addPatient}
                  className="flex-1 py-2 bg-apple-blue text-white rounded-lg text-sm font-bold"
                >
                  Add
                </button>
                <button
                  onClick={() => setShowAddPatient(false)}
                  className="flex-1 py-2 bg-white text-apple-text rounded-lg text-sm font-bold"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div className="space-y-2">
          {patients.map(p => (
            <div 
              key={p.id} 
              onClick={() => setSelectedPatient(p)}
              className={`p-4 rounded-2xl cursor-pointer transition-all ${selectedPatient?.id === p.id ? 'bg-apple-blue text-white shadow-lg' : 'bg-white hover:bg-slate-50 border border-black/[0.02]'}`}
            >
              <div className="font-bold">{p.name}</div>
              <div className={`text-xs ${selectedPatient?.id === p.id ? 'text-blue-100' : 'text-apple-secondary-text'}`}>{p.gender} • {p.dob}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="lg:col-span-3">
        {selectedPatient ? (
          <div className="journal-card bg-white p-8 md:p-12 animate-apple-fade-in">
            <div className="flex items-center justify-between mb-12">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 bg-apple-bg rounded-[2rem] flex items-center justify-center text-apple-secondary-text overflow-hidden border-4 border-white shadow-sm">
                  <img src={`https://picsum.photos/seed/${selectedPatient.id}/200/200`} alt="Patient" referrerPolicy="no-referrer" />
                </div>
                <div>
                  <h2 className="text-3xl font-bold tracking-tight">{selectedPatient.name}</h2>
                  <p className="text-apple-secondary-text font-medium">Patient ID: MS-{selectedPatient.id}00 • {selectedPatient.gender}</p>
                </div>
              </div>
              <button className="px-6 py-3 bg-apple-blue text-white rounded-2xl font-bold text-sm shadow-lg">New Record</button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
              <div className="p-6 bg-apple-bg rounded-3xl">
                <div className="text-[10px] text-apple-secondary-text font-bold uppercase tracking-widest mb-2">Last Visit</div>
                <div className="text-xl font-bold">Feb 20, 2026</div>
              </div>
              <div className="p-6 bg-apple-bg rounded-3xl">
                <div className="text-[10px] text-apple-secondary-text font-bold uppercase tracking-widest mb-2">Status</div>
                <div className="text-xl font-bold text-emerald-500">Stable</div>
              </div>
              <div className="p-6 bg-apple-bg rounded-3xl">
                <div className="text-[10px] text-apple-secondary-text font-bold uppercase tracking-widest mb-2">Next Appt</div>
                <div className="text-xl font-bold">Mar 05, 2026</div>
              </div>
            </div>

            <div className="space-y-6">
              <h3 className="text-xl font-bold tracking-tight border-b border-black/[0.03] pb-4">Recent Records</h3>
              {[
                { type: 'Diagnosis', title: 'Hypertension Stage 1', date: 'Jan 15, 2026', icon: CheckCircle2, color: 'text-red-500' },
                { type: 'Report', title: 'Blood Count (CBC)', date: 'Feb 10, 2026', icon: FileText, color: 'text-apple-blue' }
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-5 bg-apple-bg/50 rounded-2xl hover:bg-apple-bg transition-colors cursor-pointer group">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl bg-white flex items-center justify-center ${item.color} shadow-sm group-hover:scale-110 transition-transform`}>
                      <item.icon size={20} />
                    </div>
                    <div>
                      <div className="font-bold text-apple-text">{item.title}</div>
                      <div className="text-xs text-apple-secondary-text">{item.type}</div>
                    </div>
                  </div>
                  <div className="text-xs font-bold text-apple-secondary-text">{item.date}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-12 bg-white rounded-[2rem] border border-black/[0.02]">
            <Users size={48} className="text-apple-bg mb-6" />
            <h3 className="text-xl font-bold mb-2">Select a Patient</h3>
            <p className="text-apple-secondary-text max-w-xs text-sm">Choose a patient from the list to view their clinical history and records.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// --- Main App ---

export default function App() {
  const [mode, setMode] = useState<Mode>('journal');
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [isSearchyOpen, setIsSearchyOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [chartView, setChartView] = useState<'week' | 'month'>('week');
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const journalFeatures = [
    { id: 'drishti', title: 'Dr. Drishti', icon: Search, description: 'Intelligent clinical RAG search for your medical journals and research.', color: 'bg-white', accent: 'text-apple-blue', size: 'large' as const },
    { id: 'doodle', title: 'Dr. Doodle', icon: PenTool, description: 'Whiteboard for clinical sketching and diagrams.', color: 'bg-white', accent: 'text-apple-purple', size: 'normal' as const },
    { id: 'dhvani', title: 'Dhvani Sanchar', icon: Mic, description: 'Ambient clinical intelligence for real-time rounds transcription.', color: 'bg-white', accent: 'text-emerald-500', size: 'normal' as const },
    { id: 'textgen', title: 'Simple Text', icon: FileText, description: 'AI-enhanced clinical note generation.', color: 'bg-white', accent: 'text-amber-500', size: 'wide' as const }
  ];

  const patientFeatures = [
    { id: 'history', title: 'Patient History', icon: Users, description: 'Longitudinal view of patient records and history.', color: 'bg-white', accent: 'text-cyan-500', size: 'large' as const },
    { id: 'reviewer', title: 'Report Reviewer', icon: Search, description: 'Diagnostic report analysis tools.', color: 'bg-white', accent: 'text-indigo-500', size: 'normal' as const },
    { id: 'diagnosis', title: 'Diagnosis Gen', icon: CheckCircle2, description: 'Evidence-based treatment plan generation.', color: 'bg-white', accent: 'text-rose-500', size: 'wide' as const }
  ];

  const features = (mode === 'journal' ? journalFeatures : patientFeatures).filter(f => 
    f.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    f.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = (e: any) => {
      const file = e.target.files[0];
      if (file) {
        alert(`Uploading ${file.name}...`);
        // In a real app, we'd send this to the server
      }
    };
    input.click();
  };

  const renderFeatureContent = () => {
    switch (activeFeature) {
      case 'drishti': return <DrDrishti mode={mode} />;
      case 'doodle': return <DrDoodle mode={mode} />;
      case 'dhvani': return <DhvaniSanchar mode={mode} />;
      case 'textgen': return <SimpleText mode={mode} />;
      case 'history': return <PatientModeContent />;
      case 'reviewer': return <ReportReviewer />;
      case 'diagnosis': return <DiagnosisGen />;
      default: return null;
    }
  };

  const getFeatureIcon = (id: string) => {
    const f = [...journalFeatures, ...patientFeatures].find(x => x.id === id);
    return f ? f.icon : Sparkles;
  };

  const getFeatureTitle = (id: string) => {
    const f = [...journalFeatures, ...patientFeatures].find(x => x.id === id);
    return f ? f.title : 'Feature';
  };

  return (
    <div className="min-h-screen flex flex-col bg-apple-bg text-apple-text">
      {/* Header */}
      <header className="glass-header px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-apple-blue rounded-xl flex items-center justify-center text-white shadow-lg shadow-apple-blue/20">
            <Heart size={24} />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg font-bold tracking-tight">MediScribe</h1>
            <p className="text-[9px] font-bold text-apple-secondary-text uppercase tracking-widest">Clinician AI</p>
          </div>
        </div>

        <ModeToggle mode={mode} setMode={setMode} />

        <div className="flex items-center gap-3">
          <ThemeToggle isDark={isDarkMode} setIsDark={setIsDarkMode} />
          <div className="relative">
            <button 
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              className="p-2 hover:bg-black/[0.05] dark:hover:bg-white/[0.05] rounded-full text-apple-secondary-text relative"
            >
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-dark-card"></span>
            </button>
            <AnimatePresence>
              {isNotificationsOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 mt-2 w-64 bg-white dark:bg-dark-card rounded-2xl shadow-xl border border-black/[0.05] dark:border-white/[0.1] p-4 z-50"
                >
                  <h4 className="text-sm font-bold mb-3">Notifications</h4>
                  <div className="space-y-3">
                    <div className="text-xs p-2 bg-apple-bg dark:bg-white/[0.05] rounded-lg">
                      <p className="font-bold">New Report</p>
                      <p className="text-apple-secondary-text">John Doe's lab results are ready.</p>
                    </div>
                    <div className="text-xs p-2 bg-apple-bg dark:bg-white/[0.05] rounded-lg">
                      <p className="font-bold">Reminder</p>
                      <p className="text-apple-secondary-text">Surgery scheduled for 10:00 AM.</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div className="relative">
            <div 
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="w-8 h-8 rounded-full bg-slate-200 overflow-hidden border border-black/[0.05] cursor-pointer"
            >
              <img src="https://picsum.photos/seed/doc/100/100" alt="Profile" referrerPolicy="no-referrer" />
            </div>
            <AnimatePresence>
              {isProfileOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-card rounded-2xl shadow-xl border border-black/[0.05] dark:border-white/[0.1] p-2 z-50"
                >
                  <button className="w-full text-left px-4 py-2 text-sm hover:bg-apple-bg dark:hover:bg-white/[0.05] rounded-xl transition-colors">Settings</button>
                  <button className="w-full text-left px-4 py-2 text-sm hover:bg-apple-bg dark:hover:bg-white/[0.05] rounded-xl transition-colors">Profile</button>
                  <div className="h-px bg-black/[0.05] dark:bg-white/[0.1] my-1"></div>
                  <button className="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-xl transition-colors">Log Out</button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 md:p-10 max-w-6xl mx-auto w-full">
        <div className="mb-12 animate-apple-fade-in">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
                {mode === 'journal' ? 'Your Journal' : 'Patient Care'}
              </h2>
              <p className="text-apple-secondary-text text-lg max-w-xl leading-relaxed">
                {mode === 'journal' 
                  ? 'Capture clinical insights, research findings, and medical sketches in your private workspace.' 
                  : 'Access longitudinal patient records and generate evidence-based treatment insights.'}
              </p>
            </div>
            <div className="relative w-full md:w-72">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-apple-secondary-text" />
              <input 
                type="text" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search features..."
                className="w-full bg-white dark:bg-dark-card border-none rounded-2xl py-3 pl-12 pr-4 text-sm shadow-sm focus:ring-2 focus:ring-apple-blue outline-none"
              />
            </div>
          </div>
        </div>

        {/* Bento Grid Dashboard */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[200px]">
          {features.map((f, i) => (
            <FeatureCard 
              key={f.id}
              title={f.title}
              icon={f.icon}
              description={f.description}
              color={f.color}
              accentColor={f.accent}
              size={f.size}
              onClick={() => setActiveFeature(f.id)}
            />
          ))}

          {/* Upload Widget */}
          <div 
            onClick={handleUpload}
            className="journal-card bg-apple-blue text-white col-span-1 row-span-1 p-6 flex flex-col justify-center items-center text-center group cursor-pointer"
          >
            <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Upload size={24} />
            </div>
            <h4 className="font-bold">Upload Document</h4>
            <p className="text-xs text-blue-100 mt-1">PDF, Image, or Audio</p>
          </div>
          
          {/* Activity Mini Widget */}
          <div className="journal-card bg-white dark:bg-dark-card col-span-1 row-span-1 p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-apple-secondary-text uppercase tracking-widest">Activity</h4>
                <div className="flex gap-2 mt-1">
                  <button 
                    onClick={() => setChartView('week')}
                    className={`text-[10px] font-bold ${chartView === 'week' ? 'text-apple-blue' : 'text-apple-secondary-text'}`}
                  >
                    Week
                  </button>
                  <button 
                    onClick={() => setChartView('month')}
                    className={`text-[10px] font-bold ${chartView === 'month' ? 'text-apple-blue' : 'text-apple-secondary-text'}`}
                  >
                    Month
                  </button>
                </div>
              </div>
              <Activity size={16} className="text-emerald-500" />
            </div>
            <div className="text-2xl font-bold">{chartView === 'week' ? '84%' : '92%'}</div>
            <div className="h-2 bg-apple-bg dark:bg-white/[0.05] rounded-full overflow-hidden">
              <div className={`h-full bg-emerald-500 transition-all duration-500`} style={{ width: chartView === 'week' ? '84%' : '92%' }}></div>
            </div>
            <p className="text-[10px] text-apple-secondary-text">Workload efficiency is optimal</p>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="mt-12 grid grid-cols-1 lg:grid-cols-3 gap-8 animate-apple-fade-in">
          <div className="lg:col-span-2 journal-card bg-white dark:bg-dark-card p-8">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold tracking-tight">Recent Archive</h3>
              <button className="text-xs font-bold text-apple-blue uppercase tracking-widest">View All</button>
            </div>
            <div className="space-y-6">
              {[
                { id: 'drishti', title: 'ECG Analysis - P-001', type: 'Diagnostic Image', time: '2h ago', icon: FileText, color: 'text-blue-500', bg: 'bg-blue-50' },
                { id: 'dhvani', title: 'Ward 4 Patient Rounds', type: 'Voice Transcript', time: '4h ago', icon: Mic, color: 'text-emerald-500', bg: 'bg-emerald-50' },
                { id: 'history', title: 'Mitral Valve Research', type: 'Clinical Journal', time: 'Yesterday', icon: BookOpen, color: 'text-purple-500', bg: 'bg-purple-50' }
              ].map((doc, i) => (
                <div 
                  key={i} 
                  onClick={() => setActiveFeature(doc.id)}
                  className="flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-2xl ${doc.bg} ${doc.color} flex items-center justify-center group-hover:scale-110 transition-all shadow-sm`}>
                      <doc.icon size={20} />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-apple-text group-hover:text-apple-blue transition-colors">{doc.title}</div>
                      <div className="text-[10px] font-bold text-apple-secondary-text uppercase tracking-widest">{doc.type}</div>
                    </div>
                  </div>
                  <div className="text-[10px] font-bold text-apple-secondary-text">{doc.time}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="journal-card bg-apple-purple text-white p-8 flex flex-col justify-between">
            <div>
              <Sparkles size={32} className="mb-4" />
              <h3 className="text-xl font-bold mb-2">AI Summary</h3>
              <p className="text-sm text-purple-100 leading-relaxed">You have 3 reports to review and a surgery scheduled for today. Your efficiency is up by 12% this week.</p>
            </div>
            <button className="mt-6 w-full py-3 bg-white/20 hover:bg-white/30 rounded-xl text-sm font-bold transition-colors">View Daily Brief</button>
          </div>
        </div>
      </main>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 flex items-center gap-4">
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsCalendarOpen(true)}
          className="w-14 h-14 bg-white dark:bg-dark-card text-apple-text rounded-full shadow-xl flex items-center justify-center border border-black/[0.05] dark:border-white/[0.1]"
        >
          <CalendarIcon size={24} />
        </motion.button>
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsSearchyOpen(true)}
          className="fab-apple"
        >
          <Plus size={28} />
        </motion.button>
      </div>

      {/* Feature Modals */}
      <FullscreenModal 
        isOpen={!!activeFeature} 
        onClose={() => setActiveFeature(null)}
        title={getFeatureTitle(activeFeature || '')}
        icon={getFeatureIcon(activeFeature || '')}
        id={activeFeature || ''}
      >
        <div className="flex h-full">
          {/* Feature Sidebar */}
          <div className="w-64 border-r border-black/[0.05] dark:border-white/[0.05] hidden lg:flex flex-col p-6 bg-apple-bg/30 dark:bg-white/[0.02]">
            <h4 className="text-[10px] font-bold text-apple-secondary-text uppercase tracking-widest mb-6">Recent Sessions</h4>
            <div className="space-y-3 flex-1 overflow-y-auto">
              {[1, 2, 3].map(i => (
                <div key={i} className="p-4 bg-white dark:bg-dark-card rounded-2xl border border-black/[0.02] dark:border-white/[0.05] shadow-sm hover:border-apple-blue/30 transition-all cursor-pointer group">
                  <div className="text-[10px] text-apple-secondary-text font-medium mb-1 flex items-center justify-between">
                    <span>Feb 24, 11:0{i} AM</span>
                  </div>
                  <div className="text-xs font-bold text-apple-text line-clamp-1">Session Analysis #{i}</div>
                </div>
              ))}
            </div>
            <button className="mt-6 w-full py-3 bg-white dark:bg-dark-card border border-black/[0.05] dark:border-white/[0.1] rounded-xl text-xs font-bold text-apple-text hover:bg-apple-bg dark:hover:bg-white/[0.05] transition-all flex items-center justify-center gap-2">
              <Plus size={14} /> New Session
            </button>
          </div>
          {/* Feature Content */}
          <div className="flex-1 overflow-y-auto p-6 md:p-10">
            {renderFeatureContent()}
          </div>
        </div>
      </FullscreenModal>

      {/* Calendar Sidebar */}
      <AnimatePresence>
        {isCalendarOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsCalendarOpen(false)}
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
            />
            <motion.div 
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              className="fixed top-0 right-0 h-full w-full max-w-md bg-white dark:bg-dark-card shadow-2xl z-[60] p-8 flex flex-col"
            >
              <div className="flex items-center justify-between mb-8">
                <h3 className="text-2xl font-bold">Clinical Calendar</h3>
                <button onClick={() => setIsCalendarOpen(false)} className="p-2 hover:bg-apple-bg dark:hover:bg-white/[0.05] rounded-full">
                  <X size={24} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto space-y-6">
                <div className="p-6 bg-apple-bg dark:bg-white/[0.05] rounded-3xl">
                  <h4 className="text-sm font-bold mb-4">Today, Feb 24</h4>
                  <div className="space-y-4">
                    <div className="p-4 bg-white dark:bg-dark-card rounded-2xl shadow-sm border border-black/[0.02] dark:border-white/[0.05]">
                      <p className="text-xs font-bold text-apple-blue">10:00 AM</p>
                      <p className="font-bold">Cardiology Surgery</p>
                      <p className="text-xs text-apple-secondary-text">OR Room 4</p>
                    </div>
                    <div className="p-4 bg-white dark:bg-dark-card rounded-2xl shadow-sm border border-black/[0.02] dark:border-white/[0.05]">
                      <p className="text-xs font-bold text-apple-blue">02:30 PM</p>
                      <p className="font-bold">Patient Rounds</p>
                      <p className="text-xs text-apple-secondary-text">Ward 4B</p>
                    </div>
                  </div>
                </div>
              </div>
              <button className="mt-8 w-full py-4 bg-apple-blue text-white rounded-2xl font-bold shadow-lg flex items-center justify-center gap-2">
                <Plus size={20} /> Add Event
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Searchy Gooper Assistant (Simplified for Journal Theme) */}
      <AnimatePresence>
        {isSearchyOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSearchyOpen(false)}
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
            />
            <motion.div 
              initial={{ opacity: 0, y: 100, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 100, scale: 0.95 }}
              className="fixed bottom-24 left-1/2 -translate-x-1/2 w-full max-w-lg bg-white rounded-[2.5rem] shadow-2xl z-[60] overflow-hidden p-8"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-apple-purple/10 text-apple-purple rounded-2xl flex items-center justify-center">
                    <Sparkles size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold tracking-tight">Searchy Gooper</h3>
                    <p className="text-xs text-apple-secondary-text">How can I help you today?</p>
                  </div>
                </div>
                <button onClick={() => setIsSearchyOpen(false)} className="p-2 hover:bg-apple-bg rounded-full">
                  <X size={20} />
                </button>
              </div>
              <div className="space-y-4 mb-8">
                {['Summarize recent journals', 'Find Patient John Doe', 'Analyze clinical sketch', 'New clinical note'].map(action => (
                  <button key={action} className="w-full p-4 bg-apple-bg/50 rounded-2xl text-left text-sm font-semibold hover:bg-apple-bg transition-colors flex items-center justify-between group">
                    {action} <ChevronRight size={16} className="text-apple-secondary-text group-hover:translate-x-1 transition-transform" />
                  </button>
                ))}
              </div>
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Type a command or question..."
                  className="w-full bg-apple-bg border-none rounded-2xl py-4 pl-6 pr-12 text-sm focus:ring-2 focus:ring-apple-purple"
                />
                <button className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 bg-apple-purple text-white rounded-xl flex items-center justify-center shadow-lg">
                  <Send size={18} />
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
