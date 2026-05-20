Functional Requirements (what the system must do)
=================================================
1. Create Contract Definitions — users can define a contract package using existing template versions, required fields, and required documents.
2. Manage Template Versions — system must allow selection of immutable published Django contract template versions for contract generation.
3. Generate Contract Packages — system must create a ContractPackage and related ContractDocument snapshots from a CandidatePlacement.
4. Render Immutable Snapshots — generated contracts must be stored as immutable html_snapshot records.
5. Send Contracts by Email — system must email package signing links using SMTP (Mailtrap-configured).
6. Package-Level Signing — recipients must sign via one package-level tokenized signing link.
7. Signer Verification — signer must enter a name that matches the expected candidate name before signing succeeds.
8. Record Signatures — system must store signature artifacts, timestamp, and IP address in ContractSignature.
9. Manage Lifecycle States — contracts must move only through DRAFT → GENERATED → SENT → SIGNED → EXECUTED.
10. Display Live Dashboard State — dashboard must reflect real-time contract/package status.
11. Support Search — users must be able to search contracts by candidate, package ID, or status.
12. Maintain Audit Trail — every important action must create append-only ContractEvent records

Non-functional requirements
===========================
Non-Functional Requirements (how the system must behave)
Immutability — signed/generated contract snapshots and template versions must never be altered.
Traceability — every contract must be fully traceable from placement to signature to execution.
Security — signing links must use tamper-proof expirable tokens.
Reliability — invalid lifecycle transitions must fail safely (fail closed).
Consistency — all business actions must go through service-layer orchestration only.
Usability — dashboard must support full contract workflow from a single /cop interface.
Performance — dashboard searches and package loads should respond quickly under normal internal usage.
Maintainability — services must remain modular and reusable across future domains.
Scalability — architecture must support future domains (HR, investing, finance) without redesign.
Availability — local storage and SMTP failures must surface clear errors without corrupting contract state.
Auditability — system actions must be reviewable for operational and compliance purposes.
Cost Efficiency — Phase 1 must operate using local storage and built-in SMTP without external infrastructure.