# Data Processing Agreement (DPA) / Veri İşleme Sözleşmesi

This Data Processing Agreement ("Agreement") forms part of the Master Service Agreement between the Enterprise AI Platform ("Data Processor") and the Tenant ("Data Controller").

## 1. Subject Matter of Processing
The Data Processor provides a secure, air-gapped (or isolated SaaS) Artificial Intelligence and RAG (Retrieval-Augmented Generation) platform. The Processor will only process personal data strictly necessary to provide these services.

## 2. Types of Personal Data
The Data Controller may upload documents and execute chats containing:
- Names, Contact Information (Emails).
- Financial or Technical proprietary data.
- User Prompts and Chat Histories.

## 3. Obligations of the Data Processor
1. **Confidentiality:** The Processor ensures all personnel authorized to process data are bound by strict confidentiality.
2. **Security:** The Processor enforces AES-256-GCM encryption at rest, TLS 1.3 in transit, and strict Kubernetes NetworkPolicies to prevent cross-tenant data leakage.
3. **Data Subject Rights (KVKK Madde 11 / GDPR Chapter 3):** The Processor provides automated API endpoints (`/compliance/my-data`, `/compliance/delete-my-data`) enabling the Controller to instantly export or hard-delete data.
4. **Data Breach Notification:** The Processor shall notify the Controller without undue delay, and no later than 48 hours, after becoming aware of a personal data breach, assisting the Controller in meeting the 72-hour regulatory notification deadline.

## 4. Deletion of Data
Upon termination of the service, or via explicit API request ("Right to be Forgotten"), the Processor shall securely hard-delete all personal data from active PostgreSQL partitions, Qdrant vectors, and MinIO storage. Audit logs will be pseudonymized to preserve platform integrity while dropping PII.
