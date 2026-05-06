from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional

class PrivacyPolicy(BaseModel):
    policy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "1.0"
    content: str
    effective_date: datetime
    is_active: bool = True
    hipaa_compliant: bool = True
    dpdp_compliant: bool = True

class UserConsentAgreement(BaseModel):
    agreement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    policy_id: str
    agreed_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
class DataRetentionPolicy:
    """
    Data retention limits as per HIPAA and Indian DPDP norms.
    """
    MLC_RECORDS_YEARS = 10 # Medico-legal cases kept for 10 years minimum
    IPD_RECORDS_YEARS = 7 # Inpatient records kept for 7 years
    OPD_RECORDS_YEARS = 3 # Outpatient records kept for 3 years
    AUDIT_LOG_YEARS = 5 # System audit logs

# Dummy privacy policy text to serve from an endpoint
DEFAULT_PRIVACY_POLICY_TEXT = """
# Antigravity Healthcare Interoperability Platform Privacy Policy
Effective Date: 2026-05-01

1. **HIPAA & DPDP Compliance**: This platform complies with the Health Insurance Portability and Accountability Act (HIPAA) and the Digital Personal Data Protection Act (DPDPA), India.
2. **Data Minimization**: We collect only the data necessary to provide healthcare services and claim settlements.
3. **Patient Sovereignty**: Your health data belongs to you. You grant consent for specific doctors or hospitals to view your records. You can revoke this consent at any time.
4. **Data Retention**: We retain medical records in accordance with national laws (e.g., 7 years for IPD records, 10 years for Medico-Legal Cases).
5. **Data Sharing**: Data is shared with government schemes (PM-JAY, MPJAY) and insurance TPAs only when you seek admission or file a claim under those schemes.
"""
