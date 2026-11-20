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
python TD1/build_reference_td1.py
python skeleton-multi-llm-en.py --run --models <provider:model> --state state-X.jsonl --out traces-X.csv
python TD1/build_step3_td1.py
```

TD 2, from `kit-td1/` (no network, no key):

```bash
python TD2/test_vote_td2.py
python TD2/atelier-vote.py
python TD2/atelier-vote.py --traces TD1/traces-td1.csv --case C02
python TD2/compare-vote-td2.py --csv TD2/vote-comparison-td2.csv
cd TD2
python pair_b_wrong_consensus.py --export-csv
python pair_c_family_rates.py --csv family-rates-td2.csv
python atelier-routage.py
python atelier-routage.py --rule kit
```

## Completed work

TD 1: [reference-td1.csv](kit-td1/TD1/reference-td1.csv), [traces-td1.csv](kit-td1/TD1/traces-td1.csv),
[traces-td1.jsonl](kit-td1/TD1/traces-td1.jsonl), [model-question-comparison-en.csv](kit-td1/TD1/model-question-comparison-en.csv),
[five-model-summary-en.csv](kit-td1/TD1/five-model-summary-en.csv), [prompts-en.md](kit-td1/TD1/prompts-en.md),
[reports/td1.md](reports/td1.md).

TD 2: `vote_k_sur_n` in [skeleton-multi-llm-en.py](kit-td1/skeleton-multi-llm-en.py),
[vote-comparison-td2.csv](kit-td1/TD2/vote-comparison-td2.csv) (twenty decisions),
[pair-b-td2.md](kit-td1/TD2/pair-b-td2.md) (wrong consensus C02),
[routing-rule-td2.md](kit-td1/TD2/routing-rule-td2.md), simulator outputs before and after
([simulator-before-td2.jsonl](kit-td1/TD2/simulator-before-td2.jsonl),
[simulator-after-td2.jsonl](kit-td1/TD2/simulator-after-td2.jsonl)), [reports/td2.md](reports/td2.md).

## Open blocks

None for TD 1 or TD 2.
