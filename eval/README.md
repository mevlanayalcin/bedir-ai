# Citation accuracy evaluation

**Status: the harness is published and runnable; the numbers are not measured yet.**
Running it costs API calls and the Console balance is currently empty, so `results.csv` in this
repository is what a run against a credit-less endpoint produces: every question recorded as an error.
We quote no accuracy figure until a real run lands here.

## What the tool measures automatically

`run_eval.py` posts each question in `questions.json` to `/api/ask` and checks **quotation fidelity**:
every string Claude returned as `cited_text` must appear verbatim, after whitespace/case/diacritic and
Arabic harakat folding, inside the corpus entry it cites. That is a fully automatic check and it is the
one users cannot perform themselves, because a real quotation can still support nothing.

**Citation support** — does the cited passage actually back the sentence it is attached to — is a human
judgement. The CSV keeps an empty `citation_support` column for it. No automated proxy is presented as
a substitute.

## What is in the set

15 questions across Turkish, English, German and Arabic, deliberately stratified:

| kind | ids | why |
| --- | --- | --- |
| answerable from the collection | q01-q05, q08-q10, q12-q15 | measures fidelity where citations are expected |
| out of scope | q06, q07, q11 | a system that always answers is not grounded, it is confident |
| German Quran-only | q12, q13 | hadith entries carry no German text; tests the documented fallback |

## Run it

```
python3 eval/run_eval.py                     # all languages against https://bedirsavasi.com
python3 eval/run_eval.py --language tr       # one language
python3 eval/run_eval.py --base-url http://localhost:8788 --delay 0
```

The endpoint throttles per IP (8 requests / 60s), hence the 8-second default between questions.
Each run also records the model the API answered with, the documents the retrieval stage sent, and
input/cache-read token counts, so cost per question is auditable next to accuracy.
