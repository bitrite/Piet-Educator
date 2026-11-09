# Roadmap and feature status

Reviewed 9 November 2026. Planned items below are not release commitments.
The [validation record](VALIDATION.md) defines the evidence behind current claims.

## Implemented foundation

- Local Ollama/Qwen configuration and passage-based learning responses.
- Five explanation methods, retry context and gentle understanding prompts.
- Local English read-aloud, conditional highlighting and reading preferences.
- Original demo lessons and reviewed PDF/EPUB/DOCX/text/Markdown material library.
- Drafts, source references, corrections, explicit age approval and withdrawal.
- Owner library code, local persistence and source/origin/request boundaries.
- Windows source installer, desktop/Start menu launchers and separate data folder.
- Automated application/launcher tests and Windows compatibility workflow.
- Product examples, user/library/privacy guides and documentation link checks.

## Next: strengthen the supervised prototype

| Work | Why it matters | Completion evidence |
| --- | --- | --- |
| First Windows desktop smoke test | CI does not install the full stack interactively | Install, restart, model answer, import, backup and local audio checked on the target PC |
| Improve legitimate re-explanation success | Some useful retries are withheld | Broader repeated examples and human review without weakening safety/source checks |
| Broader import/accessibility evaluation | Layout and device variations can change meaning or usability | Reviewed books, tables/equations, keyboard/screen reader and voice tests |
| MindScape pilot content | Public provider descriptions are not teaching material | Permitted editions, chosen grade/subject/language and mapped reviewed passages |

## Before independent child use

- Qualified educator and safeguarding review of age bands, content and outputs.
- Protected owner/learner accounts, shared-device isolation, consent/assent and
  understandable data controls. The current owner code does not fulfil this.
- Larger adversarial and repeatability evaluation with explicit acceptance
  thresholds and no unresolved critical findings.
- A locally reviewed human-help/safeguarding process. Current phrase shortcuts
  are incomplete and do not alert another person.
- Supervised co-design and evaluation with learners, including people with ADHD,
  dyslexia or both; no inference of clinical efficacy from software checks.

## Planned learning and material capabilities

- Offline speech-to-text and spoken questions, with correction before using a
  recognition result as learner evidence.
- OCR for scans, checked diagram/equation support and richer source comparison.
- Term/topic/learning-outcome mapping and search across approved book passages.
- Bookmarks, resume/recap and carefully reviewed progress measures.
- Broader language support, voice/accent testing and optional break/task support.
- Easier library metadata maintenance and resource management.
- Font distribution/export licensing where required.
- Any support for professional-selected therapy exercises only after separate
  professional/content review. Clinical diagnosis and treatment are not current features.

There is no hosted classroom service, parent dashboard, generated image feature,
automatic marking or certified curriculum coverage in the current release.
See [curriculum scope](CURRICULUM.md) and [feature examples](README.md).
