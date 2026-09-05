/**
 * MediScribe — Clinical RAG Platform Interactive Frontend
 * Handles Doctor Background Scroll Parallax, Live Clinical RAG, Re-ranking, and Code Gen
 */

document.addEventListener('DOMContentLoaded', () => {
  initScrollParallax();
  initClinicalRAGEngine();
  initRerankingSimulator();
  initCodeGenStudio();
  initNavigationHighlighting();
});

/* ==========================================================================
   1. DOCTOR SCROLL PARALLAX & AMBIENT TRANSITION SYSTEM
   ========================================================================== */
function initScrollParallax() {
  const heroLayer = document.getElementById('parallaxHero');
  const consultLayer = document.getElementById('parallaxConsult');
  if (!heroLayer || !consultLayer) return;

  let ticking = false;

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollFraction = Math.min(1, Math.max(0, scrollTop / (docHeight || 1)));

        // Parallax transform calculations
        const heroTranslateY = scrollTop * 0.15;
        const consultTranslateY = (scrollTop - 800) * 0.12;

        // Opacity transition: Hero doctor prominent at top, consult doctor fades in as user scrolls through architecture & tools
        if (scrollTop < 800) {
          const fadeOut = Math.max(0.08, 0.22 - (scrollTop / 800) * 0.14);
          heroLayer.style.opacity = fadeOut.toFixed(3);
          heroLayer.style.transform = `scale(1.02) translateY(${heroTranslateY}px)`;
          consultLayer.style.opacity = '0';
        } else {
          heroLayer.style.opacity = '0.06';
          const consultFade = Math.min(0.24, ((scrollTop - 800) / 1200) * 0.24);
          consultLayer.style.opacity = consultFade.toFixed(3);
          consultLayer.style.transform = `scale(1.04) translateY(${Math.max(0, consultTranslateY)}px)`;
        }

        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

/* ==========================================================================
   2. CLINICAL RAG QUERY ENGINE
   ========================================================================== */
const CLINICAL_KNOWLEDGE_BASE = {
  dka: {
    query: "What is the first-line fluid resuscitation protocol for Diabetic Ketoacidosis (DKA)?",
    answer: `Based on verified clinical guidelines in the indexed medical literature:

• Initial Fluid Resuscitation: Prompt intravenous fluid resuscitation with normal saline (0.9% NaCl) at a rate of 15–20 mL/kg/hour during the first hour [Source 1: clinical_guidelines_sample.md, Page 1].
• Potassium Repletion: Potassium management is vital; if serum potassium is between 3.3 and 5.2 mEq/L, administer 20–30 mEq K+ per liter of IV fluid [Source 1: clinical_guidelines_sample.md, Page 1].
• Insulin Therapy: Regular human insulin IV infusion (0.1 units/kg/h) should only commence once serum potassium is ≥ 3.3 mEq/L to prevent fatal hypokalemic cardiac arrhythmias [Source 1: clinical_guidelines_sample.md, Page 1].`,
    citations: [
      "[Source 1: clinical_guidelines_sample.md, Page 1]",
      "[Source 2: clinical_guidelines_sample.md, Page 1]"
    ],
    triad: { faith: 0.96, ctx: 0.92, ans: 0.94 }
  },
  sepsis: {
    query: "Broad-spectrum antimicrobial timing and fluid volume in severe septic shock",
    answer: `Based on Surviving Sepsis Campaign guidelines in the indexed medical literature:

• Crystalloid Fluid Resuscitation: Immediate administration of at least 30 mL/kg of intravenous crystalloids within the first 3 hours of resuscitation [Source 1: clinical_guidelines_sample.md, Page 1].
• Antimicrobial Timing: Administration of broad-spectrum intravenous antimicrobials must be initiated within the first hour of recognition of septic shock [Source 1: clinical_guidelines_sample.md, Page 1].
• Vasopressor Support: Norepinephrine is the first-choice vasopressor to target a mean arterial pressure (MAP) ≥ 65 mmHg if hypotension persists [Source 1: clinical_guidelines_sample.md, Page 1].`,
    citations: [
      "[Source 1: clinical_guidelines_sample.md, Page 1]"
    ],
    triad: { faith: 0.98, ctx: 0.95, ans: 0.96 }
  },
  hypertension: {
    query: "What is the recommended first-line therapy for Stage 2 hypertension?",
    answer: `The provided medical textbooks do not contain sufficient evidence to answer this question.

Strict Anti-Hallucination Guardrail (Commandment 7): The indexed knowledge base currently contains Emergency Medicine and Endocrinology guidelines (DKA, Septic Shock). Because ambulatory hypertension staging guidelines are not present in the indexed blocks, no speculative answer was generated.`,
    citations: [
      "[Anti-Hallucination Shield Active: No Speculative Claim Generated]"
    ],
    triad: { faith: 1.0, ctx: 0.40, ans: 0.85 }
  }
};

function initClinicalRAGEngine() {
  const searchInput = document.getElementById('clinicalSearchInput');
  const searchBtn = document.getElementById('searchSubmitBtn');
  const synthesisContainer = document.getElementById('synthesisContainer');
  const answerBody = document.getElementById('answerBody');
  const citationsList = document.getElementById('citationsList');
  const chips = document.querySelectorAll('.query-chip');

  if (!searchInput || !searchBtn) return;

  async function executeSearch(queryText) {
    if (!queryText.trim()) return;

    searchBtn.textContent = 'Searching...';
    searchBtn.disabled = true;

    // Check if FastAPI is reachable
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, top_k: 3, rerank: true })
      });
      if (response.ok) {
        const data = await response.json();
        renderSynthesis(data.answer, data.citations);
        searchBtn.textContent = 'Search Evidence';
        searchBtn.disabled = false;
        return;
      }
    } catch (e) {
      // Local knowledge fallback
    }

    // High-fidelity fallback matching
    setTimeout(() => {
      const qLower = queryText.toLowerCase();
      let matched = CLINICAL_KNOWLEDGE_BASE.dka;
      if (qLower.includes('seps') || qLower.includes('antimicrob')) {
        matched = CLINICAL_KNOWLEDGE_BASE.sepsis;
      } else if (qLower.includes('hyperten')) {
        matched = CLINICAL_KNOWLEDGE_BASE.hypertension;
      }

      renderSynthesis(matched.answer, matched.citations);
      searchBtn.textContent = 'Search Evidence';
      searchBtn.disabled = false;
    }, 450);
  }

  function renderSynthesis(answer, citations) {
    answerBody.textContent = answer;
    citationsList.innerHTML = '';
    citations.forEach(c => {
      const li = document.createElement('li');
      li.className = 'citation-item';
      li.textContent = c;
      citationsList.appendChild(li);
    });
    synthesisContainer.style.display = 'block';
    synthesisContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  searchBtn.addEventListener('click', () => executeSearch(searchInput.value));
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') executeSearch(searchInput.value);
  });

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.getAttribute('data-query');
      searchInput.value = text;
      executeSearch(text);
    });
  });
}

/* ==========================================================================
   3. HYBRID RE-RANKING SIMULATOR
   ========================================================================== */
function initRerankingSimulator() {
  const slider = document.getElementById('weightSlider');
  const weightVal = document.getElementById('weightValDisplay');
  const rerankTable = document.getElementById('rerankTableBody');
  if (!slider || !rerankTable) return;

  const candidates = [
    { source: "clinical_guidelines_sample.md", page: 1, vec: 0.62, lexical: 0.95, medBoost: 0.90, text: "First-line fluid resuscitation for DKA consists of normal saline (0.9% NaCl) 15-20 mL/kg/h..." },
    { source: "clinical_guidelines_sample.md", page: 1, vec: 0.68, lexical: 0.45, medBoost: 0.60, text: "Potassium repletion should precede insulin therapy if serum K+ is < 3.3 mEq/L..." },
    { source: "sepsis_management.pdf", page: 4, vec: 0.58, lexical: 0.30, medBoost: 0.40, text: "Fluid challenge with crystalloids administered rapidly in hemodynamically unstable patients..." },
    { source: "pediatric_endocrinology.pdf", page: 12, vec: 0.54, lexical: 0.20, medBoost: 0.20, text: "Pediatric fluid calculation requires careful monitoring of cerebral edema signs..." },
  ];

  function calculateAndRender() {
    const vectorWeight = parseFloat(slider.value) / 100;
    const hybridWeight = 1 - vectorWeight;
    weightVal.textContent = `${Math.round(vectorWeight * 100)}% Vector / ${Math.round(hybridWeight * 100)}% Lexical+Medical`;

    const scored = candidates.map((item, origIdx) => {
      const combined = (item.vec * vectorWeight) + ((item.lexical * 0.65 + item.medBoost * 0.35) * hybridWeight);
      return { ...item, origIdx, finalScore: combined };
    });

    // Sort descending
    scored.sort((a, b) => b.finalScore - a.finalScore);

    rerankTable.innerHTML = '';
    scored.forEach((row, newIdx) => {
      const delta = row.origIdx - newIdx;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${row.source}</strong> (p.${row.page})</td>
        <td><span class="score-badge vector">${row.vec.toFixed(3)}</span></td>
        <td><span class="score-badge reranked">${row.finalScore.toFixed(3)}</span></td>
        <td>
          <span class="rank-shift" style="color: ${delta > 0 ? '#34D399' : delta < 0 ? '#F87171' : '#94A3B8'}">
            ${delta > 0 ? '▲ +' + delta : delta < 0 ? '▼ ' + delta : '— 0'}
          </span>
        </td>
        <td style="color: #94A3B8; font-size: 0.8rem;">${row.text.substring(0, 55)}...</td>
      `;
      rerankTable.appendChild(tr);
    });
  }

  slider.addEventListener('input', calculateAndRender);
  calculateAndRender();
}

/* ==========================================================================
   4. CLINICAL CODE GEN AI STUDIO
   ========================================================================== */
function initCodeGenStudio() {
  const tabs = document.querySelectorAll('.codegen-tabs .tab-btn');
  const outputBlock = document.getElementById('codeGenOutput');
  const copyBtn = document.getElementById('copyCodeBtn');
  if (!outputBlock || !tabs.length) return;

  const CODE_TEMPLATES = {
    fhir: `{
  "resourceType": "Condition",
  "id": "mediscribe-cond-8821",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "73211009",
      "display": "Diabetes mellitus"
    }],
    "text": "Type 2 Diabetes Mellitus with Ketoacidosis"
  },
  "subject": {
    "reference": "Patient/pat-9940"
  },
  "recordedDate": "2026-09-12T10:00:00Z"
}`,
    icd10: `{
  "condition_query": "Diabetic Ketoacidosis without coma",
  "icd10_cm": "E11.10",
  "icd10_display": "Type 2 diabetes mellitus with ketoacidosis without coma",
  "chapter": "IV. Endocrine, nutritional and metabolic diseases",
  "verified_grounded": true
}`,
    eval: `# MediScribe DeepEval RAG Triad Automated Test
from retrieval.retrieve_chunks import ChunkRetriever
from retrieval.evals_framework import EvalsFramework
from ingestion.store_vector_db import VectorDBStore

store = VectorDBStore()
retriever = ChunkRetriever(vector_store=store, top_k=3)
evaluator = EvalsFramework()

query = "What is the first-line fluid resuscitation protocol for DKA?"
chunks = retriever.retrieve(query)
res = retriever.synthesize_answer(query, chunks)

triad = evaluator.evaluate_rag(query, [c.text for c in chunks], res["answer"], use_llm_judge=False)
print(f"RAG Triad Summary: {triad.summary()}")
assert triad.faithfulness >= 0.60, "Faithfulness below clinical safety threshold!"
print("Test PASSED.")`
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const key = tab.getAttribute('data-template');
      outputBlock.textContent = CODE_TEMPLATES[key] || CODE_TEMPLATES.fhir;
    });
  });

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(outputBlock.textContent).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = originalText; }, 1800);
      });
    });
  }
}

/* ==========================================================================
   5. NAVIGATION HIGHLIGHTING ON SCROLL
   ========================================================================== */
function initNavigationHighlighting() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', () => {
    let current = '';
    const scrollY = window.pageYOffset;

    sections.forEach(section => {
      const sectionHeight = section.offsetHeight;
      const sectionTop = section.offsetTop - 140;
      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  }, { passive: true });
}
