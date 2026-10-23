# DIA3-3

Trustworthy generative AI (Next Generation AI), ESILV, DIA 3. Repository of sub-group
**DIA3-3**, shared from TD 1 to TD 3.

## Sub-group

| Role in TD 1 | Member |
|---|---|
| A | Edgar Merceron |
| B | Baptiste Wehry |
| C | Leo Garcia (Inès) |
| D | Nils Demougeot |
| E | Sacha Sommier |
| F | Maxence Milleker |
| G | Timothée Barselo |

Seven members, so there is no role H. Roles rotate in TD 2 and TD 3.

## Kit and data

- Pack version: **2026-10-14-students-1** (kit of 14 October 2026, in [kit-td1/](kit-td1/)).
- Database: `kit-td1/data/boutique.sqlite`, SHA-256
  `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2`, identical to
  `kit-td1/data/manifest.json` (5 products, 59 customers, 397 order lines). Never modified.
- On Windows, git may convert the CSV files of `kit-td1/data/` to CRLF, so their fingerprint no
  longer matches the manifest. Restore them with
  `git -c core.autocrlf=false checkout -- kit-td1/data/` after deleting the three CSV files.

## Environment

- Python 3.10 or later (we used 3.12), one dependency: `requests` ([kit-td1/requirements.txt](kit-td1/requirements.txt)).
- Free Groq account (members A, B, D) and two distinct free OpenRouter accounts (members C, E).
- Keys stay in environment variables, `GROQ_API_KEY` and `OPENROUTER_API_KEY`, on each
  member's machine. No key, environment file or credential is in this repository; see
  [.gitignore](.gitignore).

## Commands

From `kit-td1/`, in an activated virtual environment (`python3` on Linux/macOS, `python` on Windows):

```bash
python -m venv .venv
# Windows cmd: .venv\Scripts\activate.bat   PowerShell: .venv\Scripts\Activate.ps1   Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt

python check_access.py --no-network            # Python, database and CSV fingerprints, no call
python skeleton-multi-llm-en.py --demo         # whole chain on three simulated models, no key
python build_reference_td1.py                  # step 1: reference-td1.csv with two independent checks
python build_step3_td1.py                      # step 3: traces-td1.csv, comparison, summary, pivot

# Step 2, one operator, one model (example: A); needs the key in the environment
python skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-120b --state state-A.jsonl --out traces-A.csv
python skeleton-multi-llm-en.py --rates --state state-A.jsonl
```

Step 2 makes real calls and consumes account allowance: do not rerun it to check the hand-in.
The stored traces can be replayed offline with `--replay traces-td1.jsonl`.

## TD 1 (21 October 2026): completed work

| Artefact | Content |
|---|---|
| [kit-td1/reference-td1.csv](kit-td1/reference-td1.csv) | 20 reference queries and values, equal to the answer key (20/20) |
| [kit-td1/traces-td1.csv](kit-td1/traces-td1.csv), [kit-td1/traces-td1.jsonl](kit-td1/traces-td1.jsonl) | 105 real attempts (100 cells + 5 retries), merged from `traces-A..E.csv` and `state-A..E.jsonl`, which are kept |
| [kit-td1/model-question-comparison-en.csv](kit-td1/model-question-comparison-en.csv) | 100 final rows, one per model and question, with cause and trace pointer |
| [kit-td1/model-question-pivot-td1.csv](kit-td1/model-question-pivot-td1.csv) | Models x questions view of the comparison, for the plenary |
| [kit-td1/five-model-summary-en.csv](kit-td1/five-model-summary-en.csv) | Five models: index, prices, access, results by family |
| [kit-td1/prompts-en.md](kit-td1/prompts-en.md) | System message and user template as used, fingerprint per question |
| [kit-td1/extra-runs/](kit-td1/extra-runs/) | A second run of the Dots model made by mistake, outside the batch |
| [reports/td1.md](reports/td1.md) | Session report |

Results: gpt-oss-120b 19/20, gpt-oss-20b 18/20, qwen3.8-27b 14/20 (2 access failures),
dots-3-note 14/20, north-mini-code 12/20. Every failure is on an age question.

## Open blocks

- Cross-check between members of the reference queries: who checked which question is still
  to be recorded in `reports/td1.md`.
- Detailed contribution of members F and G still to be written in `reports/td1.md`.
