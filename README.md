# Piet Educator — local foundation

An early, single-device prototype built alongside Piet. No existing Piet files
were modified. The first curriculum source is MindScape Education, whose public
site describes CAPS-aligned homeschooling from Grade R to Grade 12. Book access,
specific editions and topic mapping are still pending. See [Curriculum scope](CURRICULUM.md).
The two original demonstration passages are not MindScape material or syllabus coverage.

## Run

**Windows:** see [Windows installation](WINDOWS-INSTALL.md). Extract the source
ZIP and double-click **Install-Windows.cmd** to set up desktop shortcuts, local
models and a separate persistent book library.

Python 3.9+ and Ollama with downloaded `qwen3:8b` weights are required. PDF import
also needs `pypdf` (`python3 -m pip install -r requirements.txt`); it is installed
on this development machine. Other supported import formats use Python's standard
library. No cloud calls or external web assets are needed. Start Ollama separately.

```sh
cd Piet-Educator
python3 server.py
```

Open http://127.0.0.1:8767. Default age band is 6–9. The device owner can start a
different learning space with `--age-band 10-12`, `--age-band 13-17` or
`--age-band adult`. Only one profile is supported per server process. No dates
of birth or diagnoses are collected. Younger children are outside this prototype.
The learner session cannot change the age, model, source text or approval status.

## Add books and learning material

Open **Add or review learning material — owner library**, or visit
http://127.0.0.1:8767/library.

1. Unlock with the library access code printed when Piet starts. Its local copy
   is in `data/owner-key`. The code is never included in the learner session or
   saved in browser storage. Use **Lock library** when finished; leaving an owner
   page unlocked gives that browser access to library actions.
2. Select PDF, EPUB, DOCX, UTF-8 text or Markdown, up to 20 MB. PDFs are limited to
   500 pages; extracted text is limited to one million characters per import.
3. Enter title, provider/author, curriculum, grade/level, subject, language and
   edition. Confirm permission to use the material. This records the owner's
   declaration, not a grant of publisher rights. The provider is not assumed to
   be MindScape merely because it is our first planned curriculum source.
4. Import creates draft passages. Review the text against the downloadable
   original, correct extraction errors, choose suitable age groups, enter a
   reviewer name and confirm the review before approving each passage.
5. Use **Refresh reading library** in the reader, then choose the book/resource
   and passage. Only approved passages for the server's age band appear. They use
   the same read-aloud and response validation as the original sample lessons.
6. Save an approved passage as draft to withdraw it. New learner questions cannot
   use revoked passages. An in-flight explanation is withheld if its passage has
   changed or been withdrawn. Text already displayed in a browser is not remotely
   erased; refresh the reading space after a review change.

The library saves original files, extracted text, corrected text, source locations
and review history under `data/`. It survives restarts. Back up the whole folder
privately; it is excluded from version control. Files have local owner permissions,
but are not encrypted by the application. `--data-dir` selects another location.

PDF references use physical file page positions, EPUB uses reading-order sections,
and Word/text resources use section/passage references rather than invented page
numbers. Diagrams, equations, tables and pagination need review. Scanned pages
are flagged when no text is found; use **Add a passage manually** for a checked
transcription. OCR, visual extraction, DRM handling and full-book question retrieval
are not implemented. Password-protected PDFs and EPUBs declaring encryption are
rejected. Imported text is never rendered as executable markup.

The owner code is a separate library capability, not verified parent identity or
a multi-user account system. Reading grade and approved age groups remain separate.

Optional named Educator model (configuration of Qwen, **not** fine-tuning):

```sh
ollama create piet-educator -f Modelfile
python3 server.py --model piet-educator --judge-model qwen3:8b
```

The application sends its full policy on every request; running the named model
alone does not enable application safeguards. Cloud-tagged models are rejected;
the adapter also checks local weight metadata before its first inference. Set
`OLLAMA_NO_CLOUD=1` in the Ollama service environment as an additional deployment
control if supported by your Ollama installation. The application itself contacts
only `127.0.0.1:11434`, ignores proxy settings and refuses HTTP redirects.

## Working foundation

- Original sample passage reader, with source always visible.
- Make it make sense: simpler explanation, steps, everyday example, verbal
  description of a picture, or an understanding question. Retry carries the last
  checked explanation and changes method; no pressure to continue.
- Age policies independent of reading preferences. Adult simplification retains
  adult language. Bands are design choices pending educator review.
- Local reading preferences: size, line spacing, theme and font. Dyslexie uses
  a locally installed copy if available; no font is bundled or licence granted.
- Local system-voice playback only, with word highlighting when the voice emits
  boundary events. No remote speech-recognition fallback. English only for now.
- Structured answer checks followed by a separate semantic review request.
  An unavailable model, malformed review, failed check or uncertainty withholds
  the generated answer. Raw drafts and review details never reach the browser.
- Learning questions and answers in memory only; presentation preferences use
  browser local storage. The material library and review history persist on disk.
  No prompt logs, audio recording, analytics or shared learner memory.
- Loopback-only server, origin/host checks, per-process request token, request
  limits, fixed static routes, restrictive browser policy and one inference at a time.

## What validation means here

1. Content catalog: explicit age eligibility, provenance, review metadata and
   approved status required. The sample passages have author approval only;
   **qualified educator review is still pending**.
2. Structure: typed fields, age-dependent length, no links/HTML and an exact
   source excerpt. An exact excerpt confirms provenance, not the answer's truth.
3. Semantic review: safety, age suitability, source grounding, preserved meaning
   and privacy must all return literal `true` before an answer is displayed.
4. Boundary regression tests: age override, draft content, fabricated citation,
   unsafe/ungrounded verdicts, malformed reviews and unavailable services.
5. Live evaluation: run `python3 evaluate_live.py --model piet-educator` with
   local Ollama. Results record outcomes only, not learner conversations.

This is not validated for independent use by children. The review pass can use the
same underlying model and therefore share its blind spots. Word and pattern
checks are supplementary and incomplete. Age suitability and factual correctness
are not guaranteed. The device owner's command line is the configuration boundary,
not verified age assurance or a parent account system. Anyone with device access
can launch another profile. The local HTTP server is for controlled development,
not school-network or multi-user deployment.

## Before a learner pilot

- Educator and safeguarding review of age bands, curriculum material and sample
  outputs. Agree how age-appropriate health, history and other sensitive education
  is reviewed rather than indiscriminately blocking topics.
- Larger adversarial tests, repeatability and independent human review, with
  explicit acceptance thresholds and no unresolved critical failures.
- Owner authentication, protected profiles, consent/assent and practical account
  isolation for shared devices; explain to children what is saved and who sees it.
- Human-help flow reviewed locally: abuse disclosures, distress, immediate danger
  and limits of confidentiality. Current shortcut is a minimal supportive message,
  not comprehensive crisis detection or an alerting service.
- Broader book-import evaluation, OCR and diagram verification. Text import with
  draft → review → approval, age eligibility and source references is implemented;
  full curriculum/topic mapping and publisher licensing remain to be completed.
- Offline speech-to-text, language/accent tests and correction before treating
  recognition output as learner answers. Playback does not establish reading ability.
- Preference persistence with reset, bookmarks, reviewed progress measures and
  learner/educator testing for ADHD and dyslexia. No clinical treatment claims.
- Font distribution/export licensing and accessibility testing across devices.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

Design references:
- [UNICEF Guidance on AI and Children](https://www.unicef.org/innocenti/reports/policy-guidance-ai-children)
- [Ollama structured chat API](https://docs.ollama.com/api/chat)

UNICEF's guidance informs the safety, privacy, inclusion and transparency design;
this prototype has not been assessed for compliance or endorsed by UNICEF.
