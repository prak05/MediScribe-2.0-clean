# 🏥 MediScribe-AI: Complete Medical AI Assistant

<div align="center">
<img width="1200" height="475" alt="MediScribe-AI Banner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

A comprehensive medical AI platform designed for healthcare professionals, featuring dual-mode operation for clinical research and patient management.

## 🚀 Quick Start

**Prerequisites:** Node.js 18+

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Add your Gemini API key to .env file
   ```

3. **Run the application:**
   ```bash
   npm run dev
   ```

4. **Access the app:** http://localhost:3000

## ✨ Features

### 🔄 Dual Mode System
- **Journal Mode**: Medical research, clinical notes, and document analysis
- **Patient Mode**: Patient management, diagnosis, and treatment planning

### 🧠 Dr. Drishti (RAG Search)
- Upload and process medical documents (PDF, images, text)
- AI-powered search across uploaded content
- Real-time chat interface for clinical queries
- Text extraction from handwriting and images

### 🎨 Dr. Doodle (Medical Whiteboard)
- Interactive drawing canvas for clinical sketches
- Anatomical diagrams and medical illustrations
- Export and save drawings
- Integration with patient records

### 🎤 Dhvani Sanchar (Voice Intelligence)
- Real-time voice recording and transcription
- Clinical note automation
- Multi-language support
- Automatic timestamping

### 📝 AI-Enhanced Text Editor
- Smart content generation
- Clinical note templates
- Export to PDF/Text formats
- AI-powered suggestions

### 👥 Patient Management
- Complete patient profiles
- Medical history tracking
- Document organization
- Appointment scheduling

### 🔍 Diagnosis Generator
- AI-powered clinical diagnosis
- Evidence-based treatment plans
- Confidence scoring
- Medication recommendations

### 📅 Smart Calendar
- Appointment scheduling
- Clinical reminders
- Integration with patient records
- Automated notifications

### 🤖 Searchy Gooper Assistant
- Floating AI assistant
- Natural language commands
- Feature navigation
- Context-aware help

## 🛠️ Technology Stack

- **Frontend**: React 19, TypeScript, Tailwind CSS
- **Backend**: Express.js, SQLite
- **AI**: Google Gemini API
- **UI/UX**: Motion animations, Responsive design
- **Database**: SQLite with full-text search
- **File Handling**: Base64 encoding, Multi-format support

## 📁 Project Structure

```
MediScribe-AI/
├── src/
│   ├── App.tsx              # Main application component
│   ├── services/
│   │   ├── api.ts           # API service layer
│   │   └── geminiService.ts # AI integration
│   └── types.ts             # TypeScript definitions
├── server.ts                # Express server
├── package.json             # Dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables
```env
GEMINI_API_KEY=your_gemini_api_key_here
APP_URL=http://localhost:3000
```

### Database Setup
The application uses SQLite for local storage. The database is automatically created on first run.

## 📋 API Endpoints

- `GET /api/patients` - Get all patients
- `POST /api/patients` - Create new patient
- `GET /api/documents` - Get documents by mode
- `POST /api/documents` - Create document
- `POST /api/upload` - Upload file
- `POST /api/rag-search` - AI search
- `POST /api/generate-diagnosis` - Generate diagnosis
- `POST /api/transcribe` - Voice transcription

## 🎯 Use Cases

### For Medical Professionals
- **Research**: Analyze medical journals and research papers
- **Clinical Notes**: Generate and organize patient notes
- **Diagnosis**: AI-assisted diagnosis and treatment planning
- **Collaboration**: Share and discuss clinical cases

### For Healthcare Institutions
- **Patient Management**: Comprehensive patient records
- **Training**: Medical education and case studies
- **Documentation**: Automated clinical documentation
- **Efficiency**: Streamline clinical workflows

## 🚀 Deployment

### Vercel Deployment
1. Push to GitHub
2. Connect to Vercel
3. Set environment variables
4. Deploy automatically

### Local Production
```bash
npm run build
npm start
```

## 🔒 Security & Privacy

- Local database storage
- No data shared with third parties
- HIPAA-compliant design principles
- Secure API key management

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📞 Support

For questions or support:
- Create an issue on GitHub
- Check documentation
- Review API endpoints

## 🏆 Awards & Recognition

Built for medical innovation hackathons and healthcare challenges.

---

**⚡ Fast • 🧠 Smart • 🔒 Secure • 🏥 Medical-Grade**

*Transforming healthcare with AI-powered medical assistance.*
