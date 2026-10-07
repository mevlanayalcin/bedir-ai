# Data notes and provenance

`data/corpus.json` is the collection the live answer endpoint passes to Claude. Each item carries its own `url`
(quran.com or sunnah.com) so any entry can be checked against the publisher independently of this repository.

## Where each text comes from

| Field in `sources` | Upstream |
| --- | --- |
| `quran_arabic` | Tanzil Uthmani text, via `api.alquran.cloud` (`quran-uthmani`) |
| `quran_tr` | Diyanet Vakfı meali, via `api.alquran.cloud` (`tr.vakfi`) |
| `quran_en` | Saheeh International, via `api.alquran.cloud` (`en.sahih`) |
| `quran_de` | Bubenheim & Elyas, via `api.alquran.cloud` (`de.bubenheim`) |
| `hadith` | Sahih al-Bukhari and Sahih Muslim (Arabic/Turkish/English), via `github.com/fawazahmed0/hadith-api`; hadith numbering follows sunnah.com |

Collection: 111 items — 41 Qur'an entries, 70 hadith entries. `version` in the file is the corpus build date, not a
release date for the product.

## Rights: what we claim and what we do not

We are **not** asserting a licence over the underlying translations. The Arabic Qur'an text is the Tanzil edition,
which is distributed under a permissive licence; the Diyanet Vakfı, Saheeh International and Bubenheim & Elyas
renderings remain with their respective publishers, and the hadith datasets are republished from an open source API.

What we publish here is the *selection, alignment and source linking* we built — the specific 111 passages about the
Battle of Badr, the four-language alignment per item, and the citation metadata the product relies on. The same file
is already downloadable from the live site, so this repository mirrors what is public; it does not widen the exposure.

Requests about attribution or removal are handled at <merhaba@bedirsavasi.com>.
