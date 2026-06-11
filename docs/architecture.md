
---

### Full Updated Content of `docs/architecture.md`

```markdown
# Architecture & Technical Design Document

**Project:** examos — Secure Minimal Arch Linux Exam Kiosk System  
**Phase:** 1 — Planning & Architecture (Completed)

---

## 1. High-Level Requirements

- Extremely minimal Arch Linux
- Per-student username + password authentication
- Double authentication inside the GTK app
- Examination instructions page before exam begins
- Real-time GPG encrypted answer saving
- Zero admin access during exam (strict lockdown)
- Controlled post-exam collection of encrypted answers only
- USB and PXE deployment support
- Fully offline after setup
- Clear documentation for different audiences

---

## 2. Core Architecture Decisions

### 2.1 Installation Type
**Chosen:** Full installation to hard disk via automated script.

**Rationale:** Required for reliable per-student accounts, persistent encrypted answer files, and strong permanent lockdown.

### 2.2 Deployment Methods
- USB boot (primary for simplicity)
- PXE network boot (for mass deployment on hundreds of machines)

Both use the same custom ISO built with archiso.

### 2.3 Encryption
**Chosen:** GPG (OpenPGP) with asymmetric public-key encryption.

**Rationale:** Industry standard. Public key distributed safely. Only central authority can decrypt.

### 2.4 GTK Application Flow

The application will use multiple views (GtkStack):

1. **Login View** — Username + Password (second authentication)
2. **Instructions View** — Exam rules + agreement checkbox + "Start Exam" button
3. **Main Exam View** — Timer, questions, answer input, auto-save, Submit button

---

## 3. Security & Lockdown Model

### During Exam
- Root account locked
- Student shell replaced with `kiosk-wrapper.sh`
- Only tty1 enabled
- No sudo or SSH
- AppArmor confinement (Phase 7)
- Full-screen GTK application

### Answer Collection
Only possible by booting the ISO in **Collection Mode**. The script copies only the encrypted `.gpg` files without allowing login or file browsing on the installed system.

---

## 4. Data Locations (Planned)

- Questions: `/opt/exam/questions/questions.json`
- Encrypted Answers: `/var/exam/answers/<username>.gpg`
- Public GPG key: `/opt/exam/keys/exam-public.asc`
- Application: `/usr/local/bin/exam_app.py` or inside `exam-app/`

---

## 5. Key Components

| Component              | Location                  | Purpose |
|------------------------|---------------------------|--------|
| Custom ISO build       | `archiso/`                | Build the deployment media |
| GTK Exam App           | `exam-app/exam_app.py`    | Student interface with double login + instructions |
| Pre-exam scripts       | `scripts/pre-exam/`       | User creation, question loading, lockdown |
| Post-exam scripts      | `scripts/post-exam/`      | Answer collection |
| Deployment scripts     | `scripts/deploy/`         | install.sh + PXE setup |
| Configuration samples  | `config/`                 | sample_students.csv, questions.json, etc. |
| Security profiles      | `security/`               | AppArmor and firewall rules (Phase 7) |

---

## 6. Future Work

- Phase 4: Implement full GTK application with the three-view flow
- Phase 5 & 6: Complete all admin and deployment scripts
- Phase 7: Add AppArmor profiles and firewall rules
- Phase 8: Comprehensive testing and final documentation

---

**This document will be updated after each major phase.**
