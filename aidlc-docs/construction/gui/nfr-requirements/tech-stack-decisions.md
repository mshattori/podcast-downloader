# Tech Stack Decisions — Unit 2: gui

## GUI Framework

| Item | Decision | Rationale |
|---|---|---|
| Framework | PySide6 (Qt 6) | Cross-platform, rich widgets, LGPL licence, official Qt Python binding |
| Confirmed in | Application Design (INCEPTION) | — |

## Additional GUI Libraries

| Purpose | Library | Notes |
|---|---|---|
| GUI framework | `PySide6>=6.6` | Already in `pyproject.toml` |
| i18n (deferred) | Qt `.ts`/`.qm` via `lupdate`/`lrelease` | Not implemented in v0.1; Japanese strings hard-coded |

## Not Adopted

| Technology | Reason |
|---|---|
| `gettext` / `.po` files | Qt-native i18n is more consistent with PySide6 workflow |
| Third-party UI libraries (e.g. `qtawesome`) | Avoid extra dependencies; standard Qt icons are sufficient |
| `QML` / `QtQuick` | `QWidget`-based UI is simpler for a desktop tool of this scope |

## Key Qt Classes Used

| Class | Usage |
|---|---|
| `QMainWindow` | Root window |
| `QSplitter` | Left/right pane layout |
| `QTableWidget` | Episode list |
| `QListWidget` | Feed list |
| `QTextEdit` (read-only) | Description pane |
| `QProgressBar` | Download progress |
| `QThread` | Background RSS fetch |
| `QMetaObject.invokeMethod` | Thread-safe GUI updates from download workers |
| `QMessageBox` | Error dialogs, confirmations |
| `QFileDialog` | Download folder selection |
| `QStatusBar` | Status messages |
| `QTranslator` | i18n (deferred) |
