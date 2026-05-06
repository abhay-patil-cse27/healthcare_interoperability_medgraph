import uuid
import base64
import structlog
from datetime import datetime, timezone
from typing import Optional
from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.documentreference import DocumentReference, DocumentReferenceContent
from fhir.resources.attachment import Attachment
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.identifier import Identifier
from fhir.resources.reference import Reference
from fhir.resources.codeablereference import CodeableReference
from fhir.resources.meta import Meta

logger = structlog.get_logger()


class FHIRService:
    def build_fhir_bundle(
        self,
        patient_id: str,
        graph_data: dict,
        llm_summary: str,
        consent_scope: str,
        request_id: str,
    ) -> dict:
        entries = []
        patient_ref = f"Patient/{patient_id}"

        # ── Patient Resource ──────────────────────────────────────────────
        patient = Patient(
            id=patient_id,
            identifier=[
                Identifier(
                    system="urn:medgraph:patient",
                    value=patient_id,
                )
            ],
            meta=Meta(
                tag=[
                    Coding(
                        system="urn:medgraph:consent",
                        code=consent_scope,
                        display=f"Consent scope: {consent_scope}",
                    )
                ]
            ),
        )
        entries.append(
            BundleEntry(
                fullUrl=f"urn:uuid:{patient_id}",
                resource=patient,
                request=BundleEntryRequest(method="PUT", url=f"Patient/{patient_id}"),
            )
        )

        # ── Condition Resources ───────────────────────────────────────────
        for cond in graph_data.get("conditions", []):
            cond_id = str(uuid.uuid4())
            icd_code = cond.get("icd10", "") or cond.get("icd10_code", "")
            coding_list = []
            if icd_code:
                coding_list.append(
                    Coding(system="http://hl7.org/fhir/sid/icd-10", code=icd_code)
                )

            condition = Condition(
                id=cond_id,
                subject=Reference(reference=patient_ref),
                code=CodeableConcept(
                    coding=coding_list if coding_list else None,
                    text=cond.get("name", "Unknown condition"),
                ),
                clinicalStatus=CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                            code=cond.get("status", "active"),
                        )
                    ]
                ),
            )
            entries.append(
                BundleEntry(
                    fullUrl=f"urn:uuid:{cond_id}",
                    resource=condition,
                    request=BundleEntryRequest(
                        method="POST", url="Condition"
                    ),
                )
            )

        # ── MedicationStatement Resources ─────────────────────────────────
        for med in graph_data.get("medications", []):
            med_id = str(uuid.uuid4())
            dosage_text = f"{med.get('dosage', '')} {med.get('frequency', '')}".strip()

            med_stmt = MedicationStatement(
                id=med_id,
                subject=Reference(reference=patient_ref),
                status="active",
                medication=CodeableReference(
                    concept=CodeableConcept(
                        text=med.get("name", "Unknown medication")
                    )
                ),
                dosage=[{"text": dosage_text}] if dosage_text else None,
            )
            entries.append(
                BundleEntry(
                    fullUrl=f"urn:uuid:{med_id}",
                    resource=med_stmt,
                    request=BundleEntryRequest(
                        method="POST", url="MedicationStatement"
                    ),
                )
            )

        # ── DocumentReference (LLM Clinical Summary) ──────────────────────
        doc_id = str(uuid.uuid4())
        summary_b64 = base64.b64encode(llm_summary.encode("utf-8")).decode("utf-8")

        doc_ref = DocumentReference(
            id=doc_id,
            status="current",
            subject=Reference(reference=patient_ref),
            type=CodeableConcept(
                coding=[
                    Coding(
                        system="http://loinc.org",
                        code="34133-9",
                        display="Summarization of episode note",
                    )
                ]
            ),
            content=[
                DocumentReferenceContent(
                    attachment=Attachment(
                        contentType="text/plain",
                        data=summary_b64,
                        title="AI Clinical Summary",
                    )
                )
            ],
            meta=Meta(
                tag=[
                    Coding(
                        system="urn:medgraph:request",
                        code=request_id,
                        display=f"Request: {request_id}",
                    )
                ]
            ),
        )
        entries.append(
            BundleEntry(
                fullUrl=f"urn:uuid:{doc_id}",
                resource=doc_ref,
                request=BundleEntryRequest(
                    method="POST", url="DocumentReference"
                ),
            )
        )

        # ── Build Bundle ──────────────────────────────────────────────────
        bundle = Bundle(
            id=str(uuid.uuid4()),
            type="transaction",
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            entry=entries,
            meta=Meta(
                tag=[
                    Coding(
                        system="urn:medgraph:consent-scope",
                        code=consent_scope,
                    ),
                    Coding(
                        system="urn:medgraph:request-id",
                        code=request_id,
                    ),
                ]
            ),
        )

        return bundle.dict()

    async def store_bundle(self, bundle_dict: dict, db) -> str:
        bundle_id = bundle_dict.get("id", str(uuid.uuid4()))
        doc = {
            "bundle_id": bundle_id,
            "bundle": bundle_dict,
            "created_at": datetime.utcnow().isoformat(),
        }
        await db["fhir_bundles"].insert_one(doc)
        logger.info("fhir_bundle_stored", bundle_id=bundle_id)
        return bundle_id
