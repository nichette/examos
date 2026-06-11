# Secure Minimal Arch Linux Exam Kiosk System

**examos** — A custom, extremely minimal, offline, and strictly locked-down Arch Linux-based exam system for national-level examinations.

Built step-by-step from scratch with security and simplicity as top priorities.

---

## Project Goal

We are building a secure exam environment that:
- Is extremely minimal (only essential components)
- Boots into a locked-down kiosk mode
- Requires student login with username + password
- Launches a custom GTK application with double authentication
- Shows examination instructions before the exam starts
- Allows students to type answers with real-time GPG encryption
- Enforces **zero admin access** during the exam
- Supports controlled collection of encrypted answers only after the exam
- Can be deployed on hundreds of computers via USB or PXE
- Is fully documented and easy to reproduce

---

## Current Status

**Phase 1: Planning & Architecture — Completed**

All core decisions have been finalized:
- Installation method: Full install to hard disk
- Deployment: USB + PXE network boot
- Encryption: GPG (OpenPGP)
- Application flow: System login → App login (username + password again) → Instructions page → Main exam
- Strict lockdown model designed

---

## How the Student Experience Works

1. Computer boots → Text login prompt appears
2. Student enters **username + password**
3. GTK exam application opens in full screen
4. **Inside the app**: Student enters **username + password again** (second authentication)
5. **Examination Instructions** page appears (rules, duration, do’s and don’ts)
6. Student agrees and clicks **Start Exam**
7. Main exam interface starts:
   - Countdown timer
   - Questions displayed
   - Answer typing area
   - Auto GPG encryption + saving every few seconds
   - Submit button
8. Exam ends → Encrypted answer file is ready for collection

---

## Architecture Overview

```mermaid
graph TD
    A[Build Machine] -->|archiso| B[Custom ISO]
    B --> C[USB or PXE Network Boot]
    C --> D[install.sh on target PCs]
    D --> E[Minimal Arch Linux on hard disk]
    E --> F[prepare_exam.sh by admin]
    F --> G[Exam Day]
    G --> H[System login]
    H --> I[GTK App: Username + Password again]
    I --> J[Instructions Page]
    J --> K[Main Exam + Auto GPG Save]
    K --> L[Submit → Encrypted file ready]
    L --> M[Post-exam Collection Mode]
