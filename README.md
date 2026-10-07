# Bedir AI

**Bedir AI** is an educational answer product over Islamic primary sources. A user asks a question in natural
language; the answer comes back with the exact verse or hadith it was drawn from, and a link to that source.

- Product (live, early access): <https://bedirsavasi.com> · [English](https://bedirsavasi.com/en/) ·
  [Deutsch](https://bedirsavasi.com/de/) · [العربية](https://bedirsavasi.com/ar/)
- Company: **Bedir AI** — operating and brand name · founded **March 2026** · Ankara, Türkiye · bootstrapped
- Founder: Mevlana Yalçın · <merhaba@bedirsavasi.com>
- Infrastructure: Cloudflare Workers + Assets (site and answer endpoint), Cloudflare KV (waitlist), Cloudflare DNS


> **Engine, honestly.** Answers are produced by `claude-haiku-4-5-20251001` on the Claude Messages API, with server-side citations and prompt caching. The endpoint has a daily token budget; past it the endpoint stops calling Claude and returns `daily_budget` until the next UTC day, and the demo shows a labelled recorded example. No other model answers.

## What Claude does in this product

The answer endpoint passes the corpus to the **Claude API as text documents with server-side citations enabled**,
one document per verse or hadith, and puts a `cache_control` breakpoint on the last document so the corpus is read
from prompt cache on repeat questions. Claude is instructed to answer only from those documents, to answer in the
language of the question, and to say when the current collection does not cover a topic instead of falling back on
parametric knowledge. The server maps returned `citations[].document_index` back onto corpus entries and the
interface renders the quoted text plus a link to quran.com or sunnah.com.

Two deliberate constraints:

- **No rulings.** Bedir AI is an information tool. It does not issue fatwas and points users to a qualified scholar
  when asked for one.
- **AI disclosure.** The answer interface states that responses are AI-generated from cited sources and may contain
  errors, consistent with Anthropic's Usage Policy for consumer-facing assistants.

## What is in this repository

This repository also holds the product itself: the static four-language site under `site/`, the answer
endpoint in `cloudflare/worker.mjs` (deployed as a Cloudflare Worker with static assets), the
citation evaluation harness in `eval/`, and the corpus builder in `scripts/`.

| Path | Contents |
| --- | --- |
| `data/corpus.json` | The full source collection the live product answers from — the same bytes served at [bedirsavasi.com/data/corpus.json](https://bedirsavasi.com/data/corpus.json) |
| `eval/README.md` | The citation-accuracy evaluation we intend to publish, with its dataset spec and metric definitions |
| `DATA_NOTES.md` | Source attributions and what we do and do not claim about the rights in the translations |

## Current scope

The first release covers the **Battle of Badr**: 41 Qur'an entries and 70 hadith entries from Sahih al-Bukhari and
Sahih Muslim, in Turkish, English, German and Arabic. Expanding to the whole Qur'an and the six canonical hadith
collections, topic-level retrieval, and the published citation-accuracy evaluation below are the next milestones.
Nothing in this repository claims those are finished.
