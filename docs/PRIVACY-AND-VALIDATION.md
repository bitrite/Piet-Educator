# Privacy, age settings and validation

Piet is a local development prototype. These controls are implemented boundaries,
not a guarantee of accuracy, clinical benefit or readiness for independent child use.

## What stays where

| Information | Current handling |
| --- | --- |
| Questions, generated answers and retry context | In application/browser memory for the visit; no application conversation history |
| Reading preferences | Browser local storage, shared by users of that browser profile |
| Study participation and review references | Memory by default; optional browser storage scoped to installation/age, not person |
| Generated study cards and reference answers | Bounded server memory cache, up to 128 cards for one hour; no learner answers cached |
| Imported originals and extracted/corrected text | Local data folder, persistent |
| Review history and reviewer names | Local SQLite database, persistent |
| Library access code | Local owner-key file; owner page holds the entered code in memory until locked/reloaded |
| Voice | Local English system-voice playback; no microphone recording or dictation pipeline |
| Model weights | Managed by local Ollama, separately from the book library |

The application has no analytics, cloud explanation fallback or outbound messaging.
It sends explanation requests to fixed `127.0.0.1:11434`, ignores proxy settings
for those calls and rejects redirects. Initial software/package/model downloads
need internet. Ollama and the operating system retain their own settings and logs;
the application does not make a blanket guarantee about other software's telemetry.

## Content checks and the answer gate

1. Imported text is draft by default. Owner approval supplies explicit age
   eligibility, reviewer information and source context.
2. The learner's server-side age setting selects eligible passages. The learner
   request cannot replace age, model or source text through the explanation API.
3. The model returns structured fields. The application checks required types,
   an age-dependent answer length, a nonempty exact source excerpt and other
   output boundaries.
4. A separate semantic review request must accept safety, age suitability,
   source grounding, preserved meaning and privacy. A false or malformed review
   withholds the generated answer. The model does not approve itself by merely
   adding a claim that its answer is safe.
5. The application rechecks the source before returning a checked answer, so
   a withdrawn or edited passage cannot supply a stale in-flight explanation.

These checks can still miss errors. Exact quotation proves that an excerpt exists,
not that every conclusion follows. Teaching and review can use the same underlying
Qwen model and share mistakes. The small live suite is not a broad safety benchmark;
some legitimate retries have been withheld. See the [validation record](../VALIDATION.md).

## Age, owner access and shared devices

The current age bands are design choices: 6–9, 10–12, 13–17 and adult. They need
educator/safeguarding review. Grade, reading level and presentation preferences
do not automatically change the age policy. Under-6 support is not implemented.

The separate owner code gates library API actions and draft/original access. It
does not establish who the person is or create a parent/teacher account. Someone
with access to the same operating-system account can read its local files or
launch another age setting. Use separate accounts where owner access must be
restricted. The library should be locked after use; it has no automatic idle lock.

The server binds to loopback and checks host/origin, request size and access
headers. That does not make it suitable for remote access, public hosting or a
shared school network. Do not expose its port as a substitute for a multi-user
deployment design.

## Support boundaries

Piet does not diagnose ADHD or dyslexia, prescribe treatment, or claim that fonts
cure dyslexia or connecting words erase memory. Any future support for exercises
chosen by a professional needs separate content and clinical review.

There is a minimal supportive human-help shortcut for certain distress phrases.
It is incomplete, does not monitor learners, does not notify a parent or educator,
and is not an emergency or safeguarding service. Appropriate education about
sensitive topics needs reviewed age-suitable sources and human oversight.

Before a child pilot: complete the account/consent design, qualified source and
output review, broader adversarial/repeatability checks, accessibility testing
and a locally reviewed safeguarding process. See the [roadmap](../ROADMAP.md).

## Study progress is not a learner account

Study display choices are browser preferences. Saving participation/review data is
separately opt-in. The record contains only totals, fixed achievement codes,
approved source references/fingerprints and selected review dates. No typed
responses, diagnoses, assessment scores or generated feedback are saved there.
Turn saving off to remove the saved record, or use the space's clear control.
Storage failures are reported rather than treated as a successful removal.

The namespace combines library installation and age band, not a person's identity.
Same-browser users of that age space share it. There are no streak penalties,
leaderboards, rewards for speed or notifications. Progress can be changed by a
person controlling the browser; it is participation, not evidence of mastery.
See [study methods](STUDY-METHODS.md) for the full data and expiry limits.

Study-card creation is checked against the approved source passage. Practice
feedback uses the card's checked practice question/reference as its immediate
evidence, with an additional activity-consistency review; this matters when a
practice example uses different numbers. Its quotation is labelled as a practice
reference rather than attributed literally to the original book. Source approval
and fingerprint are still rechecked against the original material.
