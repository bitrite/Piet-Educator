# Material library guide

The owner library adds permitted books, worksheets and other text resources to
Piet. Material enters as drafts and becomes available only through passage review.
It does not train or fine-tune the model.

## Unlock and add material

Open **Add or review learning material — owner library** from the reader, or use
the Windows **Piet Educator Library** shortcut.

For a source launch, the server prints the owner code and stores it in the chosen
data folder's `owner-key`. The Windows launcher does not print it in the learner
window; its copy is `%LOCALAPPDATA%\PietEducator\data\owner-key`. The owner can
open that file with Notepad. Never add the code or the data folder to GitHub.

1. Unlock with the code and choose one file.
2. Enter title, provider/author, curriculum framework, grade/learning level,
   subject, language and edition/year. For a MindScape resource, provider and
   CAPS framework are separate fields. Use the actual resource details.
3. Confirm permission to use the material and select **Add for review**. The
   confirmation records your declaration; it does not grant publisher rights.
4. Read extraction warnings. New passages have draft status and no age approvals.

## Supported formats and limits

| Format | Source reference | Review considerations |
| --- | --- | --- |
| PDF with selectable text | Physical PDF page and passage | Printed pages may differ; check text order, columns, equations and diagrams |
| EPUB | Reading-order section, source filename and passage | Uses spine order; images and fixed-layout details are not interpreted |
| Word `.docx` | Document text and passage | Printed pagination is not preserved; inspect tables and equations |
| UTF-8 `.txt` | Text section and passage | Plain text only |
| UTF-8 `.md` | Text section and passage | Markdown is treated as text, not rendered or executed |

Limits are 20 MB per file, 500 pages per PDF and one million extracted text
characters per import. Text is split into passages of up to about 2,400 characters;
reviewed/manual passage text can be up to 6,000 characters. Long books may need
to be split into smaller permitted files before import.

Exact duplicate files are rejected. Password-protected PDFs and EPUBs declaring
encryption are rejected. Empty/scanned pages are flagged when extraction finds
no text. OCR, image understanding, DRM handling and audio/video imports are pending.
Only the listed file types are accepted; web URLs are not a library input.

## Review and approve a passage

1. Choose the material and passage, and download the original for comparison.
2. Check the extraction against the original, particularly numbers, negation,
   instructions, tables and symbol meanings. Correct the reading text as needed.
   **Show text as originally extracted** retains the original extraction.
3. Choose suitable age groups: 6–9, 10–12, 13–17 and/or adult. These are content
   permissions, separate from curriculum grade and reading preferences.
4. Enter the reviewer name and confirm you checked the original and suitability.
5. Select **Approve this passage**. There is no whole-book auto-approval.
6. In the reader, select **Refresh reading library**, choose the book and passage.

A reviewer name records the owner's entry; it is not an authenticated educator
identity. Approving a passage does not prove curriculum alignment or teaching
quality. A child-facing pilot still needs qualified review.

## Scans, corrections and withdrawal

Use **Add a passage manually** for a checked transcription. Supply a meaningful
source location, such as “printed page 12, activity 2.” A manual passage starts
as draft; its original extraction field is empty because it was manually entered.

**Save as draft / withdraw approval** saves the current text as draft and removes
it from new learner questions. Existing browser text is not remotely erased;
refresh the reader. An answer being generated is withheld if its approved source
changes or is withdrawn before the final check.

Review records retain the submitted text, ages, status, reviewer and time. Revision
checks reject stale edits from another window. Reopen a changed passage before
reviewing again. The current UI does not edit book metadata after import or delete
books; approval withdrawal is the available learner-access control.

## Storage and moving computers

Source launches normally use the repository's `data/`; Windows installation uses
`%LOCALAPPDATA%\PietEducator\data`. The folder contains `library.sqlite3`,
`originals/` and `owner-key`. Keep the entire folder together for a private backup
while Piet is stopped. The SQLite database is not merged by copying individual
files from another library. See [Windows transfer instructions](../WINDOWS-INSTALL.md).

The library is not encrypted by the application. Keep the owner code private,
lock the library when finished and use separate operating-system accounts where
necessary. See [privacy and validation](PRIVACY-AND-VALIDATION.md).
