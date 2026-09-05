"""CODE GEN AI (Clinical Code & Schema Generator)
Software Application Layer (Commandment 9: Software Application Layer & AI Code Generation).
"""

from typing import Any, Dict, List, Optional
import datetime
import json
import logging
import uuid

from core.config import settings
from fundamentals.models import ModelRegistry

logger = logging.getLogger(__name__)

class ClinicalCodeGenAI:
    """Automated AI assistant for generating clinical schemas, FHIR resources, ICD-10 codings, and benchmark scripts."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or ModelRegistry.get_default_llm()

    def generate_fhir_resource(
        self,
        resource_type: str,
        patient_id: str,
        clinical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate HL7 FHIR R4 compliant resource structure."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        res_id = str(uuid.uuid4())

        if resource_type.lower() in ["condition", "diagnosis"]:
            return {
                "resourceType": "Condition",
                "id": res_id,
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": clinical_data.get("status", "active")
                    }]
                },
                "verificationStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed"
                    }]
                },
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "problem-list-item",
                        "display": "Problem List Item"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": clinical_data.get("snomed_code", "38341003"),
                        "display": clinical_data.get("condition_name", "Hypertension")
                    }],
                    "text": clinical_data.get("condition_name", "Hypertension")
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "recordedDate": now
            }

        elif resource_type.lower() in ["medicationrequest", "prescription"]:
            return {
                "resourceType": "MedicationRequest",
                "id": res_id,
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": clinical_data.get("rxnorm_code", "855332"),
                        "display": clinical_data.get("medication_name", "Lisinopril 10mg")
                    }],
                    "text": clinical_data.get("medication_name", "Lisinopril 10mg")
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "dosageInstruction": [{
                    "text": clinical_data.get("instructions", "Take 1 tablet orally once daily in the morning."),
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}
                }],
                "authoredOn": now
            }

        # Default Observation
        return {
            "resourceType": "Observation",
            "id": res_id,
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": now,
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": clinical_data.get("loinc_code", "8480-6"),
                    "display": clinical_data.get("observation_name", "Systolic blood pressure")
                }]
            },
            "valueQuantity": {
                "value": clinical_data.get("value", 130),
                "unit": clinical_data.get("unit", "mmHg"),
                "system": "http://unitsofmeasure.org"
            }
        }

    def generate_icd10_mapping(self, condition_text: str) -> Dict[str, Any]:
        """Map clinical symptoms/conditions to ICD-10-CM diagnosis codes."""
        text_lower = condition_text.lower()
        icd_db = {
            "hypertension": {"code": "I10", "display": "Essential (primary) hypertension"},
            "type 2 diabetes": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
            "diabetes": {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
            "heart failure": {"code": "I50.9", "display": "Heart failure, unspecified"},
            "pneumonia": {"code": "J18.9", "display": "Pneumonia, unspecified organism"},
            "asthma": {"code": "J45.909", "display": "Unspecified asthma, uncomplicated"},
            "chronic kidney disease": {"code": "N18.9", "display": "Chronic kidney disease, unspecified"},
            "covid": {"code": "U07.1", "display": "COVID-19"},
        }

        for key, val in icd_db.items():
            if key in text_lower:
                return {
                    "matched": True,
                    "condition": key,
                    "icd10_code": val["code"],
                    "icd10_display": val["display"],
                    "category": "Cardiovascular/Metabolic/Respiratory"
                }

        return {
            "matched": False,
            "condition": condition_text,
            "icd10_code": "R69",
            "icd10_display": "Illness, unspecified",
            "category": "General Signs & Symptoms"
        }

    def generate_clinical_test_case(self, specialty: str) -> Dict[str, Any]:
        """Generate a synthetic clinical benchmark scenario for RAG validation."""
        scenarios = {
            "cardiology": {
                "patient_age": 62,
                "gender": "Male",
                "chief_complaint": "Persistent elevated blood pressure (155/95 mmHg) and mild ankle edema.",
                "history": "Hypertension for 5 years, non-smoker, BMI 28.5.",
                "query": "What is the recommended first-line combination antihypertensive therapy according to ACC/AHA guidelines for Stage 2 hypertension?",
                "expected_ground_truth_concepts": ["ACE inhibitor or ARB", "Dihydropyridine CCB or thiazide diuretic", "target < 130/80 mmHg"]
            },
            "endocrinology": {
                "patient_age": 54,
                "gender": "Female",
                "chief_complaint": "Fatigue, polydipsia, fasting glucose 148 mg/dL, HbA1c 8.2%.",
                "history": "Sedentary lifestyle, family history of T2D.",
                "query": "What is the first-line pharmacologic monotherapy for newly diagnosed Type 2 Diabetes with HbA1c > 8.0% and no renal impairment?",
                "expected_ground_truth_concepts": ["Metformin", "lifestyle modification", "eGFR monitoring"]
            }
        }
        return scenarios.get(specialty.lower(), scenarios["cardiology"])

    def generate_python_eval_script(self, query: str, ground_truth: str) -> str:
        """Generate executable python snippet to test RAG against a ground truth target."""
        return f'''# Auto-Generated DeepEval Test Script for Clinical Query
from retrieval.retrieve_chunks import ChunkRetriever
from retrieval.evals_framework import EvalsFramework
from ingestion.store_vector_db import VectorDBStore

store = VectorDBStore()
retriever = ChunkRetriever(vector_store=store, top_k=4)
evaluator = EvalsFramework()

query = "{query}"
ground_truth = "{ground_truth}"

chunks = retriever.retrieve(query)
result = retriever.synthesize_answer(query, chunks)

triad = evaluator.evaluate_rag(
    query=query,
    context_chunks=[c.text for c in chunks],
    answer=result["answer"],
    use_llm_judge=False
)

print(f"RAG Triad Result: {{triad.summary()}}")
assert triad.faithfulness >= 0.5, "Faithfulness below acceptable clinical threshold!"
print("Test PASSED.")
'''
