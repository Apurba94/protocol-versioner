# protocol-versioner

**Keep lab protocols under version control without learning git: every change gets a version
number, author, date and mandatory change note; compare any two versions and export controlled copies.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Protocols evolve: incubation times change, a reagent is replaced, a step is added after a failure.
When results differ between months, the first question is "which version of the protocol did we
use?". Protocols in shared Word files lose that history. Good laboratory practice and ISO 17025 expect
document control: versioning, change records and identification of the current version.

## Features

- Protocols as Markdown, stored as `protocols/<name>/v001.md, v002.md, ...` with `history.json`
- Every update needs a change note; identical text is rejected
- Unified diffs between any two versions
- Export with a controlled-document header (title, version, date, author, status, change note)
- SHA-256 per version: edits made outside the tool are detected
- Retire protocols that are no longer in use

## Usage

```bash
pip install .
protocol-versioner add dna-extraction dna_extraction.md --author "A. Lovelace"
protocol-versioner update dna-extraction dna_extraction.md -m "Lysis 15 min instead of 10" --author ana
protocol-versioner history dna-extraction
protocol-versioner diff dna-extraction 1 2
protocol-versioner show dna-extraction -v 1 > printed_v1.md
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
