# Development and documentation upkeep

Changes should keep the implementation, feature claims, examples and operating
guides consistent. Update supporting documentation in the same change; do not
wait for a later documentation pass to describe an altered user flow or limit.

## Documentation change map

| Change | Review/update |
| --- | --- |
| Learner interaction, explanation method or reading control | README feature/example sections; [user guide](docs/USER-GUIDE.md) |
| Formats, extraction, metadata, approval, storage or backup | [Material library](docs/MATERIAL-LIBRARY.md); [architecture](docs/ARCHITECTURE.md); [privacy](docs/PRIVACY-AND-VALIDATION.md) |
| Age, owner access, network or data handling | Privacy guide; architecture; relevant user/Windows instructions |
| Installation, launch, dependency or data path | [Windows guide](WINDOWS-INSTALL.md); README setup; installer payload |
| Curriculum mapping or new teaching content | [Curriculum scope](CURRICULUM.md); provenance/permissions; relevant examples |
| Validation evidence or a known failure | [Validation record](VALIDATION.md), with scope and limits |
| Implemented/planned feature status | README; [roadmap](ROADMAP.md); [change history](CHANGELOG.md) |

## Describe features accurately

- Label implemented, demonstrated, limited and planned behaviour explicitly.
- Show a concrete input, user action and result. Mark illustrative model wording
  as illustrative; call an example verified only when evidence is recorded.
- Use original synthetic examples and anonymised screenshots. Never commit
  licensed books, learner work, private reviews, access codes or local databases.
- Keep age separate from grade/reading level. Do not turn usability preferences
  into claims of diagnosis, treatment or clinically proven outcomes.
- Record known failures rather than describing a gate rejection as a successful
  learning adaptation. Model/schema validation is not proof of truth or child safety.

## Checks

Use Python 3.9+ and install [requirements](requirements.txt). Start from the
repository root:

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_docs.py
```

The automated tests use temporary libraries and synthetic documents. They do not
need real learner data or a model download. The Windows workflow also parses and
checks the installer. After changing extraction, approval, age/access boundaries
or launcher behaviour, run the relevant tests and complete the combined suite.
For a documentation-only change, validate links and review claims against source;
do not invent a new full test run in the validation record.

For model/prompt changes, use [evaluate_live.py](evaluate_live.py) with downloaded
local models and inspect the synthetic outputs. The small live suite does not
replace human review or an adversarial evaluation. Avoid printing private inputs.

Before shipping, check `git status`, the staged file list and ignored data. If new
guides/images are linked by the README, keep them in the Windows source/payload
where appropriate. Keep generated ZIPs outside tracked source; users can always
download current source from GitHub. The installer must preserve installed books.

## Review checklist

- Does the description match the actual controls, limits and error behaviour?
- Are examples reproducible from permitted demo or reviewed material?
- Are age/access/data changes tested and their limits stated?
- Do local documentation/image links resolve?
- Are current features distinct from the roadmap?
- Are applicable guides, validation evidence and change history updated?
- Are private material and owner credentials excluded from the commit/package?

CI checks Markdown file/image destinations. It does not verify external URLs,
heading anchors, clinical claims or whether a feature actually works; those need
source review and appropriate validation.
