# Install Piet Educator on Windows

For daily use, see the [learner guide](docs/USER-GUIDE.md); for upload and approval,
see the [material library guide](docs/MATERIAL-LIBRARY.md). The [README](README.md)
contains the product description, examples and current feature boundaries.

## First installation

1. Sign into GitHub on the Windows computer and open
   [bitrite/Piet-Educator](https://github.com/bitrite/Piet-Educator).
   Choose **Code → Download ZIP**, then **Extract All** in File Explorer.
2. Open the extracted folder and double-click **Install-Windows.cmd**.
   Run it from the extracted folder, not from inside the ZIP viewer.
3. Choose the learner age setting. The installer checks for Python and Ollama,
   uses Windows Package Manager to install missing requirements, installs PDF
   support, downloads the local Qwen model and creates `piet-educator`.
   Review any software licence or permission prompts yourself.
4. Wait for the checks to finish. The first model download is approximately
   **5.2 GB**, plus the Ollama application and Python requirements.
5. Open **Piet Educator** on your Desktop or Start menu. It opens your default
   browser. Keep the accompanying Piet window open while learning; close it to
   stop the learning server.

There is also a **Piet Educator Library** shortcut for adding and reviewing books.
It opens the same owner-locked library. After the first launch, the owner access
code is stored in `%LOCALAPPDATA%\PietEducator\data\owner-key`. The owner can open
that file with Notepad and copy the code. Keep it out of learner-shared files.

This is a source-based Windows installer, not a signed MSI or Store application.
The CMD entry point runs its accompanying PowerShell script with a process-only
execution policy; it does not change the computer's saved PowerShell policy.
Managed computers may block scripts or installations; follow your administrator's
policy. Do not disable antivirus, SmartScreen or organisational controls.

## Requirements and expected behaviour

- Target: **x64 Windows**, with Windows 10 22H2 or newer as required by Ollama.
  Windows 11 is the intended desktop target. ARM installation is not supported by
  this installer. A 64-bit OS and sufficient disk space for Python, Ollama, the
  model, the app and your books are necessary.
- For initial setup, internet access is needed for missing software, the PDF
  package and model weights. Ordinary reading and local explanations then use
  the downloaded model. GPU support and response speed depend on your hardware;
  installing the app does not guarantee interactive performance on every PC.
- Windows Package Manager (`winget`) comes through Microsoft's App Installer.
  If unavailable, install [Python](https://www.python.org/downloads/windows/)
  and [Ollama](https://ollama.com/download/windows) manually, then rerun setup.
- Existing supported Python and Ollama installations are reused. Python 3.13 is
  requested only when a supported interpreter cannot be found. Software licence
  prompts are not automatically accepted. No Git installation is required.
- Downloaded local model weights are verified before launch; cloud models are
  not a fallback. If the launcher starts Ollama itself, that process disables
  cloud support. An already running Ollama instance retains its own settings.
- Local English system voices are used for playback. If none is available,
  install an offline English voice in Windows language/speech settings. Dictation
  remains pending.

Official references: [Ollama Windows requirements](https://docs.ollama.com/windows),
[Microsoft winget installation](https://learn.microsoft.com/en-us/windows/package-manager/winget/install),
[Qwen 3 8B model size](https://ollama.com/library/qwen3:8b).

## Where the Windows installation lives

| Location | Contents |
| --- | --- |
| `%LOCALAPPDATA%\PietEducator\app` | Application source and launcher |
| `%LOCALAPPDATA%\PietEducator\runtime` | Private Python environment and PDF package |
| `%LOCALAPPDATA%\PietEducator\data` | Books, extracted passages, reviews and owner code |
| `%LOCALAPPDATA%\PietEducator\settings.json` | Owner-selected age setting |

Reinstalling copies application files from an explicit allowlist. It does not
copy the source folder's `data/`, Mac virtual environments, credentials or Git
history, and does not overwrite the installed Windows library. Close Piet before
rerunning the installer. It preserves an existing valid age setting.

To change age settings, close Piet and run this from the extracted source folder
in PowerShell, selecting the intended band:

```powershell
.\windows\Install-PietEducator.ps1 -AgeBand '10-12'
```

Allowed values are `6-9`, `10-12`, `13-17` and `adult`. A running space with a
different age or data folder is not silently reused. Reading grade remains separate
from age. This owner-selected setting is not verified parent identity; use separate
Windows user accounts when children should not have owner access.

## Move your existing books separately

GitHub contains the application, not your private library. To move books already
added on the Mac:

1. Close Piet on both computers and keep a backup of both libraries.
2. Copy the complete Mac `piet-educator/data` folder privately.
3. Before adding new books on Windows, place its contents in
   `%LOCALAPPDATA%\PietEducator\data` after closing Piet. This replaces the Windows
   library; do not merge databases or overwrite a library you need to keep.
4. Restart Piet. The copied owner code, original books and passage approvals
   move together. Python and Ollama model weights are installed separately.

Windows permissions restrict the installation folder to the current account,
SYSTEM and administrators. The app does not encrypt books itself. Keep backups
and transfer media private.

## Validation limits

GitHub's Windows workflow runs the application/launcher tests, parses the installer
with Windows PowerShell, and verifies the payload layout. It does not install
Ollama, download model weights or click through Windows setup prompts. The complete
interactive installation and system-voice playback still need a Windows desktop
smoke test. Piet remains a supervised development prototype.

The installer foundation passed its [Windows compatibility run](https://github.com/bitrite/Piet-Educator/actions/runs/42602249169)
on 9 November 2026. That run exercised all 42 automated tests, PowerShell parsing,
payload validation and Python detection/invocation; it did not complete the full
interactive setup. See [validation evidence](VALIDATION.md) and the
[privacy guide](docs/PRIVACY-AND-VALIDATION.md).
