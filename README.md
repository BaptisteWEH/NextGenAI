# DIA3-3

## Sub-group

DIA3-3

## Members

- Edgar Merceron
- Baptiste Wehry
- Leo Garcia (Inès)
- Nils Demougeot
- Sacha Sommier
- Maxence Milleker
- Timothée Barselo

## Pack version

2026-10-14-students-1

## Database hash

`kit-td1/data/boutique.sqlite`, SHA-256 `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2`

## Environment

Python 3.12, `requests`; free Groq and OpenRouter accounts; keys in the environment variables
`GROQ_API_KEY` and `OPENROUTER_API_KEY`, never in the repository.

## Commands

From `kit-td1/`:

```bash
python -m pip install -r requirements.txt
python check_access.py --no-network
python build_reference_td1.py
python skeleton-multi-llm-en.py --run --models <provider:model> --state state-X.jsonl --out traces-X.csv
python build_step3_td1.py
```

## Completed work

TD 1: [reference-td1.csv](kit-td1/reference-td1.csv), [traces-td1.csv](kit-td1/traces-td1.csv),
[traces-td1.jsonl](kit-td1/traces-td1.jsonl), [model-question-comparison-en.csv](kit-td1/model-question-comparison-en.csv),
[five-model-summary-en.csv](kit-td1/five-model-summary-en.csv), [prompts-en.md](kit-td1/prompts-en.md),
[reports/td1.md](reports/td1.md).

## Open blocks

None for TD 1.
