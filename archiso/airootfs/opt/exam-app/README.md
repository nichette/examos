# Secure Examination Application

A GTK4-based kiosk exam application built for Arch Linux.

## Structure
```
examapp/
  main.py              ← entry point
  views/
    login.py           ← View 1: PAM auth + GPG decrypt
    instructions.py    ← View 2: rules + checkbox
    exam.py            ← View 3: timer + questions + autosave
    submitted.py       ← View 4: copy answers.gpg to drive
    shutdown.py        ← View 5: countdown + poweroff
  utils/
    auth.py            ← PAM password checker (never stores password)
    crypto.py          ← GPG encrypt/decrypt wrapper
    timer.py           ← Countdown + autosave timers (GLib)
  assets/
    style.css          ← GTK4 CSS theming
  examapp.service      ← systemd unit: starts app after login
  install.sh           ← one-command install on target OS
  config.example.json  ← exam configuration template
```

## Install on exam OS
```bash
sudo bash install.sh
```

## Drive layout expected
```
/media/examdrive/
  questions.gpg    ← admin places before exam
  answers.gpg      ← app writes on submit
```

## Auto-start after login
The systemd service `examapp@student` starts the app automatically
after `student` logs in to tty1.
