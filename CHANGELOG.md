# Change history

This project is a development prototype. Entries describe repository changes;
they do not imply a certified or production-ready release.

## Documentation expansion — 9 November 2026

- Expanded the product description, intended audiences, current feature table,
  screenshots and practical feature examples in the README.
- Added learner, library, privacy/validation and architecture guides, a roadmap
  and contributor documentation requirements.
- Corrected curriculum notes to reflect implemented imports and pending outcome
  mapping; clarified source versus Windows owner-code and storage behaviour.
- Added local Markdown link checks to CI and included supporting documentation
  in the Windows installation payload.

## Windows setup — 9 November 2026

Foundation commit: `5b3dc1a`.

- Added `Install-Windows.cmd`, a per-user PowerShell installer and Desktop/Start
  menu shortcuts for reading and library management.
- Added local requirement/model checks, installed age configuration and separate
  application/runtime/data folders with Windows account permissions.
- Added Windows installation and private book-transfer instructions.
- Automated suite increased to 42 tests; GitHub Windows tests, PowerShell parsing
  and Python detection/invocation checks passed. Full interactive installation
  and Windows audio remain target-device checks.

## Initial learning and library foundation — 9 November 2026

Foundation commit: `1ab7e31`.

- Added a local Piet Educator model configuration, original sample lessons,
  age-dependent response policies and a checked explanation flow.
- Added reading preferences, local read-aloud and five explanation methods.
- Added draft imports, source references, passage correction/review, age approval,
  withdrawal and owner-gated access to the persistent material library.
- Recorded six basic live-model outcomes and an upload-to-learning browser example.
- Created the private repository, excluding books, owner codes and local databases.
