"""Build data/corpus.json from downloaded public datasets.

Usage: python3 -I scripts/build_corpus.py <download_dir> <out.json>
Quran: api.alquran.cloud (quran-uthmani, tr.vakfi, en.sahih, de.bubenheim)
Hadith: github.com/fawazahmed0/hadith-api (ara/tur/eng editions)
"""
import json, sys, os

src, out = sys.argv[1], sys.argv[2]

QURAN_RANGES = {3: [(12, 13), (121, 127)], 8: [(1, 19), (41, 48), (67, 71)]}
SURAH = {3: ("Âl-i İmrân", "Āl ʿImrān", "Āl ʿImrān", "آل عمران"),
         8: ("Enfâl", "Al-Anfāl", "Al-Anfāl", "الأنفال")}
EDITIONS = {"ar": "quran-uthmani", "tr": "tr.vakfi", "en": "en.sahih", "de": "de.bubenheim"}
MUSLIM = [4588, 4915]  # dataset numbers -> Abdul Baqi 1763, 1901


def surah(ed, s):
    d = json.load(open(os.path.join(src, f"q_{ed}_{s}.json"), encoding="utf-8"))
    return {a["numberInSurah"]: a["text"] for a in d["data"]["ayahs"]}


def hadiths(name):
    d = json.load(open(os.path.join(src, f"h_{name}.json"), encoding="utf-8"))
    return {h["hadithnumber"]: h for h in d["hadiths"]}


items = []
for s, ranges in QURAN_RANGES.items():
    texts = {lang: surah(ed, s) for lang, ed in EDITIONS.items()}
    for a0, a1 in ranges:
        for a in range(a0, a1 + 1):
            ar = texts["ar"][a]
            if a == 1 and ar.startswith("بِسْمِ"):
                pass
            items.append({
                "id": f"Q{s}:{a}", "type": "quran",
                "title": {"tr": f"{SURAH[s][0]} {s}:{a}", "en": f"Qur'an {s}:{a} ({SURAH[s][1]})",
                          "de": f"Koran {s}:{a} ({SURAH[s][2]})", "ar": f"{SURAH[s][3]} {s}:{a}"},
                "url": f"https://quran.com/{s}/{a}",
                "text": {lang: texts[lang][a].strip() for lang in EDITIONS},
            })

for coll, nums in (("bukhari", None), ("muslim", MUSLIM)):
    E, T, A = hadiths(f"eng-{coll}"), hadiths(f"tur-{coll}"), hadiths(f"ara-{coll}")
    if nums is None:
        nums = [n for n in range(3949, 4030) if n in E and "Badr" in E[n]["text"]]
    for n in nums:
        num = E[n]["arabicnumber"] if coll == "muslim" else n
        num = int(num) if float(num).is_integer() else num
        text = {"ar": A.get(n, {}).get("text", ""), "tr": T.get(n, {}).get("text", ""), "en": E[n]["text"]}
        text = {k: v.strip() for k, v in text.items() if v and v.strip()}
        tr_name, en_name = ("Buhârî", "Sahih al-Bukhari") if coll == "bukhari" else ("Müslim", "Sahih Muslim")
        items.append({
            "id": f"{coll[0].upper()}{num}", "type": "hadith",
            "title": {"tr": f"{tr_name} {num}", "en": f"{en_name} {num}", "de": f"{en_name} {num}",
                      "ar": ("صحيح البخاري " if coll == "bukhari" else "صحيح مسلم ") + str(num)},
            "url": f"https://sunnah.com/{coll}:{num}",
            "text": text,
        })

corpus = {
    "name": "Bedir AI demo corpus — Battle of Badr",
    "version": "2026-10-07",
    "sources": {
        "quran_arabic": "Tanzil Uthmani text via api.alquran.cloud (quran-uthmani)",
        "quran_tr": "Diyanet Vakfı meali (tr.vakfi) via api.alquran.cloud",
        "quran_en": "Saheeh International (en.sahih) via api.alquran.cloud",
        "quran_de": "Bubenheim & Elyas (de.bubenheim) via api.alquran.cloud",
        "hadith": "Sahih al-Bukhari & Sahih Muslim (ara/tur/eng) via github.com/fawazahmed0/hadith-api; numbering as on sunnah.com",
    },
    "items": items,
}
json.dump(corpus, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
q = sum(1 for i in items if i["type"] == "quran")
print(f"{len(items)} items ({q} ayat, {len(items) - q} hadith) -> {out}")
