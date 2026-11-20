# TD 1 - Five models on the same twenty questions

Session of 21 October 2026. Statement: [enonce-td1-en](enonce-td1-en.html). Report:
[reports/td1.md](../../reports/td1.md).

The files below are listed in the order of the work: each step uses the output of the previous one.

## 1. The questions and the reference values

| File | Role |
|---|---|
| [questions-td1-en.md](questions-td1-en.md), `questions-td1.json` | The twenty questions C01 to C20 (kit files, no answers) |
| [build_reference_td1.py](build_reference_td1.py) | Runs our twenty reference queries on `../data/boutique.sqlite` (read-only) and checks each value two other ways |
| [reference-td1.csv](reference-td1.csv) | **Output:** the query and the value in cents of each question, with who checked it |

## 2. One batch per model (one operator per model)

| File | Role |
|---|---|
| [prompts-en.md](prompts-en.md) | System message and user template, exactly as used |
| `traces-A.csv` ... `traces-E.csv` | Raw attempts of each operator: A `gpt-oss-120b`, B `gpt-oss-20b`, C `north-mini-code:free`, D `qwen3.8-27b`, E `dots-3-note-preview:free` |
| `state-A.jsonl` ... `state-E.jsonl` | The matching state files written by `../skeleton-multi-llm-en.py --run` |
| [extra-runs/](extra-runs/README.md) | A real run outside the 100-cell batch (wrong model by mistake), kept apart |

## 3. Consolidation and results

| File | Role |
|---|---|
| [build_step3_td1.py](build_step3_td1.py) | Merges the five batches and produces the summaries below |
| [traces-td1.csv](traces-td1.csv), [traces-td1.jsonl](traces-td1.jsonl) | **All 105 real attempts** (100 cells + 5 retries). Every later step, TD 2 included, reads these |
| [model-question-comparison-en.csv](model-question-comparison-en.csv) | One final row per model and question: verdict, explanation, pointer to the trace |
| [model-question-pivot-td1.csv](model-question-pivot-td1.csv) | The same as a models x questions matrix |
| [five-model-summary-en.csv](five-model-summary-en.csv) | The five models: index, dated prices, access, results per family |
| [comparison-example-en.md](comparison-example-en.md) | Kit example of the column definitions (fictional values) |

## Replay

From `kit-td1/`:

```bash
python TD1/build_reference_td1.py      # step 1, no network
python TD1/build_step3_td1.py          # step 3, from the five stored batches, no network
```

Step 2 needs the API keys and one operator per model (see the statement); its outputs are stored here,
so the next steps never need to call a model again.

**Next:** [TD 2](../TD2/README.md) uses `traces-td1.csv` and `reference-td1.csv` to build the vote and the routing rule.
