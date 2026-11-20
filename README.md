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

## How to read this repository

Each TD builds on the previous one. Read in this order:

1. **Setup:** [kit-td1/README.md](kit-td1/README.md). The course kit: database, questions,
   shared skeleton, environment guide.
2. **TD 1, comparing five models:** [kit-td1/TD1/README.md](kit-td1/TD1/README.md), which goes from
   reference values to the batches to the consolidated traces. Report: [reports/td1.md](reports/td1.md).
3. **TD 2, vote and routing:** [kit-td1/TD2/README.md](kit-td1/TD2/README.md). It covers the k-of-n
   vote on the TD 1 traces, then the wrong consensus, then the routing rule and the simulator.
   Report: [reports/td2.md](reports/td2.md).
4. **TD 3, cost and choice of a configuration:** [kit-td1/TD3/](kit-td1/TD3/) (statement and cost
   method; work to come on 11 December).

| Folder | Content |
|---|---|
| `kit-td1/` | Shared kit files: `skeleton-multi-llm-en.py` (with our `vote_k_sur_n`), `sandbox_sqlite.py`, `data/`, `check_access.py` |
| `kit-td1/TD1/`, `TD2/`, `TD3/` | Statement, our code and our evidence for each session |
| `reports/` | One session report per TD |
| `templates/` | Blank hand-in forms from the kit |
| `lectures/` | Course slides |

## Environment

Python 3.12, `requests`; free Groq and OpenRouter accounts; keys in the environment variables
`GROQ_API_KEY` and `OPENROUTER_API_KEY`, never in the repository.

## Commands

TD 1, from `kit-td1/` (the run step needs the API keys; its outputs are stored in `TD1/`):

```bash
python -m pip install -r requirements.txt
python check_access.py --no-network
python TD1/build_reference_td1.py
python skeleton-multi-llm-en.py --run --models <provider:model> --state TD1/state-X.jsonl --out TD1/traces-X.csv
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
