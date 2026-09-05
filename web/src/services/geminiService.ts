import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

export const geminiModel = "gemini-3-flash-preview";

export async function generateRAGResponse(query: string, context: string) {
  const response = await ai.models.generateContent({
    model: geminiModel,
    contents: `
      Context: ${context}
      
      Question: ${query}
      
      Instructions: Answer strictly based on the provided context. If the information is not in the context, say "Insufficient information in your documents." Cite sources if applicable.
    `,
  });
  return response.text;
}

export async function generateDiagnosis(notes: string) {
  const response = await ai.models.generateContent({
    model: geminiModel,
    contents: `
      Clinical Notes: ${notes}
      
      Task: Generate a structured diagnosis and treatment plan based on these notes.
      Format: JSON with fields: diagnosis, plan, medications, confidence_score (0-1).
    `,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          diagnosis: { type: Type.STRING },
          plan: { type: Type.STRING },
          medications: { type: Type.ARRAY, items: { type: Type.STRING } },
          confidence_score: { type: Type.NUMBER }
        },
        required: ["diagnosis", "plan", "medications", "confidence_score"]
      }
    }
  });
  return JSON.parse(response.text || "{}");
}

export async function transcribeAudio(audioBase64: string) {
  // In a real app, we'd use a dedicated STT model or Gemini's audio capability.
  // For this MVP, we'll simulate it or use Gemini's multimodal if enabled.
  // Since we don't have a real audio stream here, we'll return a placeholder.
  return "Simulated transcription: Patient reports mild chest pain and shortness of breath.";
}
