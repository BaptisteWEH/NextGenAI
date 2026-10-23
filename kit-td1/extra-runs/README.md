# Extra run, outside the 100-cell batch

`traces-dots-run2-by-operator-C.csv` holds **20 real calls** to
`openrouter:dots-studio/dots-3-note-preview:free`, made on 2026-10-21 from 13:57:49 to
13:59:46 UTC by operator C, who meant to run `cohere/north-mini-code:free`. The wrong
`--models` value was used. The file was first pushed as `kit-td1/traces-C.csv` (commit
`116ff8b`), then replaced by the real Cohere batch. It is restored here byte for byte from
that commit, because the protocol keeps every real attempt.

- It is **not** part of the 100 cells: the final results of model E come from
  [traces-E.csv](../traces-E.csv) only, and these rows are not in `traces-td1.csv` nor in
  `model-question-comparison-en.csv`.
- It used 20 OpenRouter calls of operator C's account, counted separately from the batch.
- Its state file was not pushed; only the CSV export exists.
- Same model, same prompt fingerprints, temperature 0: 13/20 correct here against 14/20 in
  `traces-E.csv`, with 5 questions changing verdict (C08, C11, C17, C18, C19). This is an
  observation of run-to-run variability on two runs, not a measured rate.
