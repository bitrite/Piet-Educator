# Foundation verification — 9 November 2026

Status: development prototype; not approved for independent use by children.

## Verified

- 17 automated domain and HTTP boundary tests passed. The final policy wording
  change was followed by another pass of the 13 domain tests; HTTP code was unchanged.
- JavaScript syntax check passed using the bundled Node runtime.
- Installed `piet-educator:latest` using the existing Qwen 3 8B weights. This is a
  separate model configuration, not trained educational weights.
- Final live suite: 6/6 automated cases passed with `piet-educator` generating
  and local `qwen3:8b` reviewing. Original synthetic questions only.
- Child and adult explanations displayed checked responses. Unknown shopkeeper
  name was acknowledged as absent. The arrival question correctly preserved
  uncertainty. Direct policy override was redirected; harm request was withheld.
- Live generation/review cases took approximately 6–12 seconds on this machine
  in the final suite. This is not a performance guarantee.
- Browser inspection confirmed readable layout, sample lesson, immutable age
  label, local voice availability, submitted question, displayed explanation,
  source excerpt and retry controls. Local audio playback and word-boundary
  timing have not been independently verified by listening.
- Browser retry switched from a plain explanation to steps, but that generated
  attempt was withheld. This verifies the closed gate, not successful adaptation.
  Over-withholding on legitimate re-explanation remains an open usability issue;
  the six-case live smoke suite does not cover the full iterative learning loop.

## Interpretation and limitations

The live suite checks specific outcomes, not comprehensive safety. A missing fact
may be withheld or acknowledged explicitly; it must not be invented. Exact source
quoting does not verify every statement. The review pass uses the same underlying
Qwen model, so shared mistakes remain possible. Earlier runs found an unnecessary
rejection of an uncertainty question and inconsistent harmful-request status;
the application policy and response schema were tightened, then the suite rerun.

No child users, personal data, licensed books, voice recordings or private
learning histories were used in testing. There has been no clinical efficacy,
curriculum alignment, legal compliance or child-safety certification.

Next gates: qualified content/safeguarding review, broader adversarial evaluation,
repeatability, protected owner/learner accounts, accessibility checks and
supervised learner testing. See README.md for the remaining product work.

## Material library verification — 9 November 2026

- Final combined suite: **36 tests passed**, including the existing learning
  boundaries and new extraction, persistence, approval and HTTP access tests.
- Both browser scripts passed JavaScript syntax checks.
- Synthetic PDF with selectable text preserved physical page references; a blank
  page was flagged. A password-protected PDF was rejected. EPUB spine order and
  script exclusion, Word text extraction and XML-entity rejection were exercised.
- Confirmed drafts do not enter the reader, age-ineligible approvals stay hidden,
  correction retains original extracted text, duplicate files are rejected and
  originals survive a library restart. Approval requires review confirmation and
  at least one explicit age group. Stale revisions cannot overwrite newer reviews.
- Confirmed learner session tokens cannot read draft details/originals, import
  files or approve passages. Owner access uses a separate local capability code.
- Confirmed withdrawn passages cannot answer stale learner questions, including
  withdrawal while an explanation is being prepared.
- Browser flow verified using `tests/fixtures/import-demo.txt`, an original Piet
  resource explicitly labelled as a demonstration. Uploaded as draft, absent
  from reader, approved by prototype author, refreshed into reader, and answered
  by local Piet with the exact excerpt “Three counters are blue.”

No licensed MindScape content or real learner information was imported. The owner
code is not a verified parent account. PDF/EPUB/Word extraction is text-only;
manual source checking remains necessary for layout, diagrams, equations and
scans. OCR, full-book retrieval and independent learner readiness are pending.

## Windows setup foundation — 9 November 2026

- Added a source-based Windows installer, desktop/Start menu launchers, separate
  installed data location and Windows permissions. Installer uses explicit WinGet
  package IDs and leaves licence prompts interactive.
- Combined local suite: **42 tests passed**, including Windows UTF-8 BOM settings,
  paths with spaces, invalid-age rejection, local-model checks and matching an
  existing server's age and data location before reuse.
- GitHub Windows workflow runs the same suite, parses the installer with Windows
  PowerShell, validates its payload and exercises Python detection/invocation.
- No interactive Windows installation, WinGet prerequisite installation, Windows
  GPU model run or system-voice playback has been performed on this Mac. These
  remain target-device smoke checks; automated compatibility is narrower.

## Documentation upkeep — 9 November 2026

- Added product examples and linked learner, material-library, privacy and
  architecture guides, plus roadmap, change history and contribution requirements.
- Corrected curriculum import status and Windows/source owner-code descriptions.
- Added local Markdown file/image destination checks to the Windows workflow.
- Extended the Windows payload allowlist so installed guides retain their local
  source/documentation/image links. This does not copy private material or credentials.
- Documentation link checks validate destinations, not external URLs, heading
  anchors, clinical statements or actual feature behaviour. Examples are labelled
  illustrative or verified against the recorded synthetic demonstrations.

## Study and gentle participation slices — 11 November 2026

- Final local application suite: **63 tests passed**. Added study-card structure,
  source/age access, expiry/eviction, hidden suggested answers, action tokens,
  edited/withdrawn source handling, feedback context and activity consistency checks.
- **7 JavaScript state tests passed**: assistance earns equal completion credit,
  elapsed days do not subtract participation, revoked/revised references are removed,
  stored state excludes learner answers, rewards can be off, and voluntary review
  dates can be replaced/removed. JavaScript syntax and documentation links checked.
- All six methods produced checked cards from the original sharing sample in a
  live run. An adult teach-back activity also passed. This is narrow synthetic
  coverage, not proof of learning benefit or comprehensive safety.
- Live inspection caught two failures despite checked model outputs: spelling
  correction in meaning practice, and feedback answering the source example when
  the practice question used different numbers. Added explicit meaning instructions,
  supplementary style rejection, separate practice-reference evidence and a required
  activity-consistency review. Worked practice then used five each for ten counters
  shared between two people, rather than four from the original twelve/three example.
- Re-ran the original six explanation/safety smoke cases on the shared validation
  code; all six passed.
- Practice quotations are explicitly labelled as derived checked references, not
  literal book excerpts. Original material approval/fingerprints remain enforced.
  Writing-demand or claimed-understanding wording uses explicit reference support
  through the same gate, rather than pretending to assess the learner.
- Browser checks confirmed Explore → Try → Reflect, optional covering, a checked
  hint, explicit answer support, untimed pause/resume, equal one-completion credit,
  optional review reference and garden. With saving off, reloading removed this
  synthetic visit's participation/review state while reading preferences remained.
- No real learner responses, private curricula or clinical data were used. Source
  snapshots and participation counters do not establish mastery. Feedback wording
  and mathematical/educational correctness still need independent review.

Spaced review currently uses user-selected dates, not a performance-adaptive
algorithm. Saved browser state is shared by the same installation/age/browser,
not isolated by learner identity. Dictation, authenticated profiles and broader
learner/safeguarding evaluation remain pending. The Windows installer includes
study assets; CI also exercises the JavaScript state checks.
