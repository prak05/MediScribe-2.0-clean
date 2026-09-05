import express from "express";
import { createServer as createViteServer } from "vite";
import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";
import { GoogleGenAI } from "@google/genai";
import fs from "fs";
import crypto from "crypto";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const db = new Database("mediscribe.db");

// Initialize Gemini AI
const ai = process.env.GEMINI_API_KEY ? new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY }) : null;

// Document storage for RAG
const documentStore = new Map(); // In-memory for MVP - in production use vector DB

// Initialize Database
db.exec(`
  CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dob TEXT,
    gender TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    patient_id TEXT,
    title TEXT NOT NULL,
    content TEXT,
    type TEXT NOT NULL, -- 'pdf', 'image', 'note', 'scribble', 'voice'
    mode TEXT NOT NULL, -- 'journal', 'patient'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
  );

  CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    patient_id TEXT,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
  );

  CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    feature TEXT NOT NULL,
    query TEXT,
    response TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Routes
  app.get("/api/patients", (req, res) => {
    const patients = db.prepare("SELECT * FROM patients ORDER BY created_at DESC").all();
    res.json(patients);
  });

  app.post("/api/patients", (req, res) => {
    const { id, name, dob, gender } = req.body;
    db.prepare("INSERT INTO patients (id, name, dob, gender) VALUES (?, ?, ?, ?)").run(id, name, dob, gender);
    res.json({ success: true });
  });

  app.get("/api/documents", (req, res) => {
    const { mode, patient_id } = req.query;
    let query = "SELECT * FROM documents WHERE 1=1";
    const params = [];
    if (mode) {
      query += " AND mode = ?";
      params.push(mode);
    }
    if (patient_id) {
      query += " AND patient_id = ?";
      params.push(patient_id);
    }
    query += " ORDER BY created_at DESC";
    const docs = db.prepare(query).all(...params);
    res.json(docs);
  });

  app.post("/api/documents", (req, res) => {
    const { id, patient_id, title, content, type, mode } = req.body;
    db.prepare("INSERT INTO documents (id, patient_id, title, content, type, mode) VALUES (?, ?, ?, ?, ?, ?)").run(id, patient_id, title, content, type, mode);
    res.json({ success: true });
  });

  app.get("/api/appointments", (req, res) => {
    const appointments = db.prepare(`
      SELECT a.*, p.name as patient_name 
      FROM appointments a 
      LEFT JOIN patients p ON a.patient_id = p.id 
      ORDER BY start_time ASC
    `).all();
    res.json(appointments);
  });

  app.post("/api/appointments", (req, res) => {
    const { id, patient_id, title, type, start_time, end_time } = req.body;
    db.prepare("INSERT INTO appointments (id, patient_id, title, type, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)").run(id, patient_id, title, type, start_time, end_time);
    res.json({ success: true });
  });

  app.get("/api/history", (req, res) => {
    const { feature } = req.query;
    const history = db.prepare("SELECT * FROM history WHERE feature = ? ORDER BY created_at DESC").all(feature);
    res.json(history);
  });

  app.post("/api/history", (req, res) => {
    const { id, feature, query, response } = req.body;
    db.prepare("INSERT INTO history (id, feature, query, response) VALUES (?, ?, ?, ?)").run(id, feature, query, response);
    res.json({ success: true });
  });

  // RAG Search API
  app.post("/api/rag-search", async (req, res) => {
    try {
      const { query, mode } = req.body;
      
      if (!ai) {
        return res.json({ answer: "AI service not available. Please configure GEMINI_API_KEY." });
      }
      
      // Get documents for the current mode
      const docs = db.prepare("SELECT * FROM documents WHERE mode = ? ORDER BY created_at DESC LIMIT 10").all(mode);
      
      // Build context from documents
      const context = docs.map(doc => `Title: ${doc.title}\nContent: ${doc.content}`).join('\n\n');
      
      if (!context) {
        return res.json({ answer: "No documents found. Please upload some content first." });
      }
      
      const response = await ai.models.generateContent({
        model: "gemini-1.5-flash",
        contents: `
          Context: ${context}
          
          Question: ${query}
          
          Instructions: Answer strictly based on the provided context. If the information is not in the context, say "Insufficient information in your documents." Be concise and accurate.
        `,
      });
      
      res.json({ answer: response.text });
    } catch (error) {
      console.error('RAG search error:', error);
      res.status(500).json({ error: 'Search failed' });
    }
  });

  // Document processing API
  app.post("/api/process-document", async (req, res) => {
    try {
      const { content, type } = req.body;
      
      if (!ai) {
        return res.json({ processedContent: "AI processing not available. Please configure GEMINI_API_KEY." });
      }
      
      const response = await ai.models.generateContent({
        model: "gemini-1.5-flash",
        contents: `
          Process this ${type} content and convert it to clean, readable text:
          
          ${content}
          
          Instructions: Extract all text, convert handwriting to text if applicable, describe charts/graphs, and format cleanly.
        `,
      });
      
      res.json({ processedContent: response.text });
    } catch (error) {
      console.error('Document processing error:', error);
      res.status(500).json({ error: 'Processing failed' });
    }
  });

  // Diagnosis generation API
  app.post("/api/generate-diagnosis", async (req, res) => {
    try {
      const { notes, patientId } = req.body;
      
      if (!ai) {
        return res.json({ 
          diagnosis: {
            diagnosis: "AI diagnosis not available. Please configure GEMINI_API_KEY.",
            plan: "Manual review required.",
            medications: [],
            confidence_score: 0,
            recommendations: "Configure API key for AI-powered diagnosis."
          }
        });
      }
      
      // Get patient history if available
      let patientContext = "";
      if (patientId) {
        const patientDocs = db.prepare("SELECT * FROM documents WHERE patient_id = ?").all(patientId);
        patientContext = patientDocs.map(doc => `Title: ${doc.title}\nContent: ${doc.content}`).join('\n\n');
      }
      
      const response = await ai.models.generateContent({
        model: "gemini-1.5-flash",
        contents: `
          Patient Notes: ${notes}
          Patient History: ${patientContext}
          
          Task: Generate a structured diagnosis and treatment plan based on these notes.
          Format as JSON with fields: diagnosis, plan, medications, confidence_score (0-1), recommendations.
        `,
        config: {
          responseMimeType: "application/json",
        }
      });
      
      res.json({ diagnosis: JSON.parse(response.text || "{}") });
    } catch (error) {
      console.error('Diagnosis generation error:', error);
      res.status(500).json({ error: 'Diagnosis generation failed' });
    }
  });

  // File upload handling
  app.post("/api/upload", express.json({ limit: '10mb' }), (req, res) => {
    try {
      const { mode, title, type, patientId, content } = req.body;
      const id = crypto.randomUUID();
      
      // Store file info in database
      db.prepare("INSERT INTO documents (id, patient_id, title, content, type, mode) VALUES (?, ?, ?, ?, ?, ?)")
        .run(id, patientId, title, content, type, mode);
      
      // Store in memory for RAG (in production, use proper vector DB)
      documentStore.set(id, { content, mode, title });
      
      console.log('Document uploaded successfully:', { id, title, mode, type });
      res.json({ success: true, documentId: id });
    } catch (error) {
      console.error('Upload error:', error);
      res.status(500).json({ error: 'Upload failed' });
    }
  });

  // Voice transcription API
  app.post("/api/transcribe", async (req, res) => {
    try {
      const { audioData } = req.body;
      
      // For MVP, simulate transcription
      // In production, integrate with actual STT service
      const transcription = "Simulated transcription: " + audioData.substring(0, 100) + "...";
      
      res.json({ transcription });
    } catch (error) {
      console.error('Transcription error:', error);
      res.status(500).json({ error: 'Transcription failed' });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, "dist")));
    app.get("*", (req, res) => {
      res.sendFile(path.join(__dirname, "dist", "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
