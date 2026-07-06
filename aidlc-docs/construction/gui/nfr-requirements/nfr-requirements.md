# Non-Functional Requirements — Unit 2: gui

## Inherited from Unit 1: core

| Requirement | Value |
|---|---|
| Python version | 3.11+ |
| Target OS | Windows 10+, macOS 12+, Ubuntu 22.04+ |
| Logging | RotatingFileHandler, 5 MB × 3 generations |
| Error handling | Fail-fast with user notification; no silent failures |

---

## NFR-GUI-01: UI Responsiveness

| Requirement | Value |
|---|---|
| App launch to window visible | < 3 seconds |
| Feed list click → episode table populated from cache | < 200 ms |
| RSS fetch | Background thread; UI remains interactive |
| Download | Background thread; UI remains interactive |
| Main thread blocking | Zero — all I/O must run off the main thread |

---

## NFR-GUI-02: Visual / Usability

| Requirement | Value |
|---|---|
| Minimum window size | 800 × 600 px |
| Default window size | 1024 × 768 px |
| Window resize | Fully resizable; table columns adapt via stretch |
| High-DPI support | Enable `Qt.AA_EnableHighDpiScaling` |
| Font | System default |

---

## NFR-GUI-03: Internationalisation

| Requirement | Value |
|---|---|
| Initial release | Japanese hard-coded in source |
| i18n framework | Deferred — Qt `.ts`/`.qm` approach planned for a future release |
| Date format | `YYYY-MM-DD HH:MM` (ISO, locale-neutral) |
| Number format | Plain integers (no locale-specific separators needed) |

---

## NFR-GUI-04: Accessibility

| Requirement | Value |
|---|---|
| `data-testid` attributes | All interactive elements carry a stable `data-testid` (see `frontend-components.md`) |
| Keyboard navigation | Standard Qt tab order; no custom key traps |

---

## NFR-GUI-05: Thread Safety

| Requirement | Value |
|---|---|
| GUI updates from worker threads | Always via `QMetaObject.invokeMethod(..., Qt.QueuedConnection)` |
| Direct widget mutation from non-main thread | Forbidden |
