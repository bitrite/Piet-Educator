# Architecture and operating boundaries

Piet Educator is a standalone Python/browser application built alongside Piet.
The browser talks to a loopback HTTP server; the server calls local Ollama and
maintains a local SQLite material library. There is no hosted backend or
multi-user identity system in this version.

## Components

| Component | Responsibility |
| --- | --- |
| [server.py](../server.py) | HTTP routes, loopback binding, request boundaries and application composition |
| [educator.py](../educator.py) | Age policies, explanation methods, local Ollama adapter and response gate |
| [study.py](../study.py) | Checked study cards, source fingerprints and bounded in-memory activity cache |
| [library.py](../library.py) | Original-file storage, draft passages, transactional reviews and eligible lessons |
| [extract_material.py](../extract_material.py) | Isolated text extraction for supported document formats |
| [windows_launcher.py](../windows_launcher.py) | Installed configuration, model readiness and matching an existing learning space |
| [Windows installer](../windows/Install-PietEducator.ps1) | Per-user installation, prerequisites, shortcuts, permissions and checks |
| [Reader](../web/app.js) | Resource/passage selection, questions, retries, presentation and local speech playback |
| [Owner library](../web/library.js) | File upload, metadata entry, review, transcription and approval withdrawal |
| [lessons.json](../lessons.json) | Original author-approved demonstration passages; educator review pending |

## Learning request flow

1. The browser reads `/api/session`, receiving the server-selected age, eligible
   lessons and a learner request token. The owner code is not in that response.
2. `/api/explain` accepts lesson ID, question, method and previous checked
   explanation. It resolves approved source text on the server rather than
   accepting replacement text or an age supplied by the learner.
3. The fixed loopback Ollama adapter verifies local model metadata and asks for
   structured output. The source and learner text are treated as untrusted data
   in the teaching/review instructions, not authoritative policy changes.
4. Structural checks and a semantic review determine whether to show the answer.
   A final source lookup withholds it if the passage was edited or withdrawn.
5. The browser displays plain text, source excerpt and a validation limitation.
   It does not render model output as executable HTML.

Only one explanation is processed at a time. Learning content/answers are not
automatically saved as a learner history or fine-tuning dataset.

## Material flow

Uploads carry file bytes plus metadata. The server checks owner access, type,
size, permission declaration and duplicate content digest. Extraction runs in a
separate Python process with a wall timeout; CPU/resource limits are applied
where the operating system supports them. Documents are not executed, EPUB
scripts are omitted and no document links are fetched.

Originals use generated storage names. Extraction creates draft passages with
source locations. Owner review records corrected text, exact reviewed revision,
ages, reviewer and time in one SQLite transaction. Revision conflicts reject
stale reviews. Eligible lesson selection uses approved status and the running
age setting; grade is descriptive metadata, not the age access rule.

## Storage

| Store | Contents |
| --- | --- |
| `data/originals/` | Original imported bytes with generated names |
| `data/library.sqlite3` | Materials, draft/approved passages and review snapshots |
| `data/owner-key` | Persistent library capability code |
| Browser local storage | Presentation preferences only |
| Request/browser memory | Current question, answer and retry context |
| Study-card cache | Generated source-bound teaching cards, up to 128 for one hour; no learner responses |
| Optional browser practice storage | Participation totals, fixed badges, source IDs/fingerprints and voluntary review dates |
| Ollama model store | Downloaded model weights, outside the application library |

`--data-dir` changes source-launch library location. Windows keeps installed data
outside `app/`, under `%LOCALAPPDATA%\PietEducator\data`. Copying or publishing
the source does not move private books. See [backup/transfer](MATERIAL-LIBRARY.md).

## HTTP surface

| Route | Purpose | Access |
| --- | --- | --- |
| `GET /api/session` | Eligible reading resources and local session information | Trusted local host/origin |
| `POST /api/explain` | Explain a selected approved passage | Learner token |
| `POST /api/study/create` | Generate and check a study card from an approved passage | Learner token |
| `POST /api/study/action` | Request a hint, explicit suggested answer or checked feedback | Learner token |
| `GET /api/library` | List local materials and review counts | Owner code |
| `POST /api/library/import` | Upload a supported file as draft | Owner code |
| `GET /api/library/{id}` | Read draft/review details | Owner code |
| `GET /api/library/{id}/original` | Download the original bytes | Owner code |
| `POST /api/library/{id}/passages` | Add a manual draft transcription | Owner code |
| `POST /api/library/passages/{id}/review` | Save draft or approve the submitted revision | Owner code |

These are local prototype routes, not a versioned public integration API. The
owner capability is not a role/account service. See [privacy and validation](PRIVACY-AND-VALIDATION.md).

## Study slices

Card generation reuses `Educator.checked_result`, the shared structural and semantic
response gate. All card fields are checked before public question/scaffolding fields
are returned; suggested answers remain on the server until explicit support or
feedback. Every action re-resolves age-eligible content and its fingerprint. Feedback
requests are not retained in the card cache. The browser records participation,
not correctness, and refreshes source eligibility before finishing an activity.

For feedback on a derived practice problem, the checked question/reference becomes
the immediate model/review evidence. The original approved source is still checked
for age eligibility, edits and withdrawal. Responses explicitly label this derived
practice quotation and require an additional `activity_consistent` review result.

`web/study-state.js` contains testable participation/review state rules; `web/study.js`
provides the quest UI and opt-in browser persistence. Its storage namespace combines
installation and age, not a verified learner identity. See [study methods](STUDY-METHODS.md).
