#!/usr/bin/env python3
"""Citation-accuracy harness for Bedir AI.

Runs questions.json against the live /api/ask endpoint and computes *quotation fidelity*
automatically: every quoted string must appear verbatim in the corpus entry it cites.
Citation *support* (does the passage actually back the sentence) needs human labels; the
results CSV leaves citation_support empty for that reason, and we never report it as measured.

Usage:
    python3 eval/run_eval.py                       # all questions against the live site
    python3 eval/run_eval.py --language tr         # one language
    python3 eval/run_eval.py --base-url http://localhost:8788
    python3 eval/run_eval.py --out eval/results.csv

The endpoint is throttled per IP (8 requests / 60s), so the default delay between questions is
8 seconds; lower it only if you know the throttle is off.
"""

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DECLINE_MARKERS = {
    "tr": ["kapsamıyor", "kapsamıyor olabilir", "bu ilk sürüm", "yer vermiyor"],
    "en": ["does not cover", "not covered", "does not address", "in this first release"],
    "de": ["deckt die aktuelle", "nicht ab", "in dieser ersten"],
    "ar": ["لا تغطي", "لا تشمل", "هذا الإصدار"],
}


def normalize(text: str) -> str:
    """Fold whitespace, case, diacritics and Arabic harakat so verbatim checks are fair."""
    out = unicodedata.normalize("NFKD", (text or "").lower())
    out = "".join(c for c in out if not unicodedata.combining(c))
    out = re.sub(r"[\u064b-\u0652\u0670]", "", out)  # Arabic harakat and superscript alef
    table = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u", "ß": "ss"})
    out = out.translate(table)
    out = re.sub(r"[^\w\s\u0600-\u06ff]", " ", out, flags=re.UNICODE)
    return re.sub(r"\s+", " ", out).strip()


def ask(base_url: str, question: str, lang: str, timeout: int = 120):
    body = json.dumps({"q": question, "lang": lang}).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/ask",
        data=body,
        headers={"content-type": "application/json", "user-agent": "bedir-eval/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}") if e.fp else {}
    except Exception as e:  # network / timeout
        return 0, {"error": f"{type(e).__name__}: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://bedirsavasi.com")
    ap.add_argument("--language", choices=["tr", "en", "de", "ar"], help="run one language only")
    ap.add_argument("--only", help="comma separated question ids")
    ap.add_argument("--delay", type=float, default=8.0, help="seconds between requests")
    ap.add_argument("--out", default=str(HERE / "results.csv"))
    args = ap.parse_args()

    corpus = json.loads((REPO / "data" / "corpus.json").read_text(encoding="utf-8"))
    by_id = {i["id"]: i for i in corpus["items"]}
    qs = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))["questions"]
    if args.language:
        qs = [q for q in qs if q["language"] == args.language]
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        qs = [q for q in qs if q["id"] in want]

    rows, answered, declined, failed, total_cites, faithful = [], 0, 0, 0, 0, 0
    for n, q in enumerate(qs, 1):
        status, data = ask(args.base_url, q["question"], q["language"])
        if status != 200 or "answer" not in data:
            failed += 1
            print(f"{n:>2} {q['id']} [{q['language']}] FAILED http={status} {str(data)[:110]}")
            rows.append({**q, "outcome": "error", "citations": 0, "faithful": "", "detail": str(data)[:200]})
            continue

        text_joined = " ".join(p.get("text", "") for p in data["answer"])
        cites = [c for p in data["answer"] for c in p.get("cites", [])]
        checks = []
        for c in cites:
            item = by_id.get(c.get("id"))
            if not item:
                checks.append(False)
                continue
            src = item["text"].get(q["language"]) or item["text"].get("en") or ""
            checks.append(normalize(c.get("quote", "")) in normalize(src))
        declined_like = not cites and any(m in text_joined.lower() or m in text_joined for m in DECLINE_MARKERS[q["language"]])
        outcome = "decline" if declined_like else "answer"
        answered += outcome == "answer"
        declined += outcome == "decline"
        total_cites += len(cites)
        faithful += sum(1 for c in checks if c)
        miss = [c.get("id") for c, ok in zip(cites, checks) if not ok]
        print(
            f"{n:>2} {q['id']} [{q['language']}] {outcome:7} cites={len(cites):2} "
            f"fidelity={sum(checks)}/{len(checks) if checks else 0} "
            f"docs={data.get('retrieval', {}).get('documents_sent', '?')} "
            f"tok_in={data.get('usage', {}).get('input', '?')} "
            f"cache_read={data.get('usage', {}).get('cache_read', '?')}"
            + (f"  NOT_VERBATIM:{miss}" if miss else "")
        )
        rows.append({
            **q,
            "outcome": outcome,
            "citations": len(cites),
            "faithful": sum(checks),
            "answer_chars": len(text_joined),
            "documents_sent": data.get("retrieval", {}).get("documents_sent", ""),
            "model_returned": data.get("model", ""),
            "citation_support": "",
            "detail": ";".join(miss),
        })
        if n < len(qs) and args.delay:
            time.sleep(args.delay)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["id"])
        w.writeheader()
        w.writerows(rows)

    print("\n--- özet ---")
    print(f"soru={len(qs)} cevap={answered} ret={declined} hata={failed}")
    if total_cites:
        print(f"atıf: {total_cites}   alıntı sadakati (birebir kaynakta bulunan): {faithful}/{total_cites} = {faithful/total_cites:.1%}")
    else:
        print("atıf üretilemedi: endpoint yanıt vermedi (API kredisi gerekiyor olabilir)")
    print(f"CSV: {args.out}")
    print("Not: citation_support insan etiketi ister, bu araç ölçmez.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
