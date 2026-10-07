#!/usr/bin/env python3
"""Generates the four language homepages from one template + translation table.

The site was previously four hand-maintained copies, which is how the language versions drifted
apart (one of them said Istanbul while the account said Ankara). Keeping the copy in one place
makes the drift impossible by construction: run this, then scripts/build_pages.sh.

    python3 scripts/build_site.py            # writes site/{,en,de,ar}/index.html
    python3 scripts/build_site.py --check    # fail if committed files differ from the template

Content rules enforced here: no metric we cannot show, no source we cannot name, and the engine
(Claude, or the labelled backup) is stated rather than implied.
"""

import argparse
import hashlib
import json
import pathlib
import sys
from html import escape

REPO = pathlib.Path(__file__).resolve().parent.parent
GITHUB = "https://github.com/mevlanayalcin/bedir-ai"
LI = "https://www.linkedin.com/in/mevlanayalcin/"

T = {
    "tr": dict(
        locale="tr", dir_="ltr", title="Bedir AI • Kaynağını Gösteren Yapay Zekâ İslami Bilgi Asistanı",
        desc="Kur'an ve hadis sorularına, her cümlenin dayandığı âyeti veya hadisi ve kaynağa bağlantıyı göstererek yanıt veren yapay zekâ asistanı. Anthropic Claude API üzerinde kurulu.",
        nav=dict(ask="Soru sor", docs="API dokümanı", product="Ürün", how="Nasıl çalışır", corpus="Koleksiyon", api="Kurumsal", company="Kurumsal bilgi", contact="İletişim"),
        hero=dict(
            eyebrow="CLAUDE API · ATIFLI YANIT", h1a="Kaynak atıflı yanıtlar:", h1b="Kur'an ve hadis soruları için.",
            sub="Kurgulanmış bir koleksiyon üzerinde çalışan soru-cevap asistanı ve HTTP API'si. Her yanıt, dayandığı âyeti veya hadisi yayıncı bağlantısıyla açar. Denetleyebilirsin; değiştiremezsin.",
            ex_label="KAYDEDİLMİŞ ÖRNEK", ex_apilink="API isteginin ve yanıtının tamamı", ex_q="Bedir'de yardım hangi âyette geçiyor?", ex_a="Kur'an 3:123, Bedir'de yardım olunduğunu söylüyor.", ex_title="Kur'an 3:123 (Âl-i İmrân)", ex_pub="Tanzil · Diyanet Vakfı meali",
            cta_demo="Örnek kaydı gör", cta_api="API dokümantasyonu",
            preview_label="ÖRNEK SORU VE KAYNAK", preview_q="Bedir'deki yardımı hangi âyet anlatır?",
            preview_ans="Âl-i İmrân 3:123, Bedir'de yardım edildiğini anlatır. [1]", preview_src="[1] Âl-i İmrân 3:123 · Kaynağı aç ↗"),
        proof=["41 âyet + 70 hadis: Bedir koleksiyonu", "Kapsama: ar · en · tr tam, de 41/111"],
        example=dict(h2="Bir kere sor, iki kere denetle", lead="Numaralı her im, cevabın dayandığı metni ve yayıncıya bağlantısını açar. Aşağıdaki, koleksiyondan birebir alıntılanmış gerçek bir kayıt.",
                     note="Atıf, cevabın doğru olduğunu garanti etmez — kontrol edebileceğin bir şeyi garanti eder."),
        how=dict(h2="Nasıl çalışır", lead="Uydurma bir cevap yerine, ne olduğunu gösteren bir hat.",
                 steps=[("Koleksiyon", "Kur'an metni Tanzil (Osmanlı) nüshasından, Türkçe Diyanet Vakfı, İngilizce Saheeh International, Almanca Bubenheim & Elyas mealinden gelir; hadisler Buhârî ve Müslim açık veri kümelerinden, numaralar sunnah.com ile hizalı."),
                        ("Belge olarak Claude'a", "Her âyet ve hadis ayrı bir belge olarak, sunucu taraflı atıflar etkin şekilde Claude API'ye geçirilir. Son belgeye cache_control eklenir ki koleksiyon yinelenen sorularda prompt cache'ten okunsun."),
                        ("Atıflı cevap", "Claude yalnızca verilen belgelerden cevaplamakla, sorunun dilinde yazmakla ve koleksiyon bir soruyu kapsamıyorsa bunu söylemekle yükümlüdür; ezber bilgisine düşmez."),
                        ("Ekranda alıntı", "Arayüz her atfın alıntıladığı metni, kaynağın başlığını ve quran.com / sunnah.com bağlantısını gösterir; cevabın kendisi düz metindir.")]),
        audience=dict(h2="Kimin için", lead="İlk sürüm Bedir Gazvesi ile sınırlı; odaklandığımız iş, ders hazırlayan birinin kaynağı tek adımda görmesidir.",
                      cards=[("Ders hazırlayanlar", "Bir konu için âyet ve hadis adayı bul, sonra alıntıyı bağlamında oku. Kopyala-yapıştır değil, tıklayarak doğrula."),
                             ("Kendi başına okuyanlar", "Doğal dille sor; cevabın hangi metne dayandığını gör; kitap ve tefsir taraflı okuma için bağlantıyı kullan."),
                             ("Erken araştırma", "Bir konuda başlangıç noktası bul; cevap, alıntı ve kaynağı birlikte incele; hataları raporla.")],
                      api_h3="Okullar ve çalışma platformları için", api_lead="Koleksiyonumuz genişledikçe, atıflı yanıtı ürünlerinde göstermek isteyenler için bir API açacağız.",
                      api_items=["İsteğe göre metin + alıntı + yayıncı URL'si döner", "Hangi dilden ve hangi koleksiyon sürümünden yanıt verildiği cevapla birlikte gelir", "Yanıtlanamayan soru uydurulmaz; işaretlenir", "Kurumsal deneme için merhaba@bedirsavasi.com"],
                      api_cta="Kurumsal deneme için yaz"),
        corpus=dict(h2="Bedir koleksiyonu", lead="Yanıt verirken kullandığımız metinlerin tamamı, kaynaklarıyla birlikte açıktır.",
                    th_src="Kaynak", th_desc="Açıklama",
                    rows=[("Kur'an (Arapça)", "Tanzil Uthmani metni, api.alquran.cloud üzerinden"),
                          ("Kur'an (Türkçe)", "Diyanet Vakfı meali (tr.vakfi)"),
                          ("Kur'an (İngilizce)", "Saheeh International (en.sahih)"),
                          ("Kur'an (Almanca)", "Bubenheim & Elyas (de.bubenheim)"),
                          ("Hadis", "Sahîh-i Buhârî ve Sahîh-i Müslim; fawazahmed0/hadith-api; numaralar sunnah.com ile hizalı")],
                    note="Çevirilerin telifi yayıncılarındır; burada yayımladığımız şey seçkimiz, dört dilli hizalamamız ve atıf meta verimizdir. Tek dosya: /data/corpus.json"),
        roadmap=dict(h2="Yol haritası (durumuyla)", lead="Ne bitti, ne sürüyor, ne sadece tasarlandı — ayırt ediyoruz.",
                     items=[("Yayında", "Bedir Gazvesi koleksiyonu üzerinde atıflı yanıt: 41 Kur'an, 70 hadis kaydı; TR/EN/DE/AR."),
                            ("Sürmekte", "Tüm Kur'an ve altı hadis koleksiyonuna genişleme; konu bazlı geri getirme."),
                            ("Tasarlandı, henüz koşmadı", "Yayımlanacak atıf doğruluğu değerlendirmesi: alıntı sadakati ile atfın iddiayı desteklemesi ayrı ölçülür."),
                            ("Sırada", "İslam okulları ve çalışma platformları için atıflı yanıt API'si; mobil uygulama.")]),
        wait=dict(h2="Gelişmelerden haberdar ol", lead="Koleksiyon büyüdükçe ve API açıldıkça haber veririz.",
                  ph="e-posta adresin", btn="Listeye katıl", privacy="Adresin tek satır halinde Cloudflare'da saklanır; merhaba@bedirsavasi.com ile sildirilebilir. Reklam postası yok."),
        faq=dict(h2="Sık sorulanlar", items=[
            ("Fetva veriyor musunuz?", "Hayır. Bedir AI bir bilgi aracıdır; bağlayıcı dinî hüküm istiyorsan yetkin bir âlime yönlendirir."),
            ("Hangi modeli kullanıyorsunuz?", "Ürün Claude API üzerinde kuruludur. Console hesabında bakiye kalmadığı dönemlerde demo, yanıtın üstünde belirtilen etiketli bir yedek modelle çalışır; yedek yanıt Claude atfı olarak sunulmaz."),
            ("Yanıtlar hatalı olabilir mi?", "Evet. Atıf, alıntının kaynakta gerçekten geçtiğini ölçülebilir kılar; cümlenin tamamının doğruluğunu garanti etmez."),
            ("Verilerimi saklıyor musunuz?", "Sohbet geçmişi tutmuyoruz. Listeye yazıldığında sadece e-posta adresin saklanır."),
            ("Neden sadece Bedir?", "Kapsamlı bir koleksiyon, dar bir konu üzerinde doğrulanabilir şekilde kurulduğunda güvenilirdir. Genişleme sürüyor.")]),
        legal="Bedir AI · Ankara, Türkiye · 2026 · işletme adı (tescilli tüzel kişilik değil) · <a href=\"mailto:merhaba@bedirsavasi.com\">merhaba@bedirsavasi.com</a>",
        disclosure="Bir kişiyle değil, yapay zekâ asistanıyla konuşuyorsunuz. Yanıtlar atıf gösterilen kaynaklardan üretilir ve hata içerebilir.",
        fatwa_note="Bedir AI bir bilgi aracıdır, fetva vermez. Bağlayıcı dinî hüküm için yetkin bir âlime danışın.",
        count_note="şu ana kadar katılan"),
    "en": dict(
        locale="en", dir_="ltr", title="Bedir AI • The AI Islamic Knowledge Assistant That Shows Its Sources",
        desc="An AI assistant for Qur'an and hadith questions that shows the verse or hadith behind every answer, with a link to the publisher. Built on Anthropic's Claude API.",
        nav=dict(ask="Ask", docs="API docs", product="Product", how="How it works", corpus="Corpus", api="For institutions", company="Company", contact="Contact"),
        hero=dict(
            eyebrow="CLAUDE API · CITED ANSWERS", h1a="Cited answers for", h1b="Qur'an and hadith questions.",
            sub="A question-answering assistant and an HTTP API over a curated collection. Every answer opens the exact verse or hadith it rests on, with a link to the publisher. You can audit it; you cannot edit it.",
            ex_label="RECORDED EXAMPLE", ex_apilink="See the API request and response", ex_q="Which verse describes the help given at Badr?", ex_a="Qur'an 3:123 states that help was given at Badr.", ex_title="Qur'an 3:123 (Āl ʿImrān)", ex_pub="Tanzil · Saheeh International",
            cta_demo="See a worked example", cta_api="API documentation",
            preview_label="EXAMPLE QUESTION AND SOURCE", preview_q="Which verse describes the help given at Badr?",
            preview_ans="Qur'an 3:123 states that help was given at Badr. [1]", preview_src="[1] Qur'an 3:123 · Open the source ↗"),
        proof=["41 verses + 70 hadith, scoped to the Battle of Badr", "Coverage: ar · en · tr complete, de 41 of 111"],
        example=dict(h2="Ask once, audit twice", lead="Every numbered marker opens the text the answer was drawn from and its publisher link. Below is a real record quoted verbatim from the collection.",
                     note="A citation does not guarantee the answer is correct. It guarantees something you can check."),
        how=dict(h2="How it works", lead="A pipeline you can inspect, instead of an invented answer.",
                 steps=[("The collection", "Qur'anic text from the Tanzil Uthmani edition; Turkish Diyanet Vakfı, English Saheeh International and German Bubenheim & Elyas renderings; hadith from open datasets of Sahih al-Bukhari and Sahih Muslim, numbered as on sunnah.com."),
                        ("Passed to Claude as documents", "Each verse and hadith is sent to the Claude API as a separate document with server-side citations enabled. A cache_control breakpoint on the last document lets the collection be read from prompt cache on repeat questions."),
                        ("A cited answer", "Claude must answer from those documents only, in the language of the question, and say when the collection does not cover a topic instead of falling back on memorised knowledge."),
                        ("The quotation, on screen", "The interface shows the quoted text, the source title and a link to quran.com or sunnah.com for every citation.")]),
        audience=dict(h2="Who it is for", lead="The first release is scoped to the Battle of Badr. The job we care about is a teacher finding a passage and checking it in one step.",
                      cards=[("Educators", "Find verse and hadith candidates for a topic, then read the quotation in context. Verify by clicking, not by trusting."),
                             ("Independent readers", "Ask in natural language, see what the answer is based on, and follow the link for a fuller reading."),
                             ("Early research", "Find a starting point, inspect answer, quotation and source together, and report the mistakes.")],
                      api_h3="For schools and study platforms", api_lead="As the collection grows we will open an API that returns cited answers for products that need them.",
                      api_items=["Returns text plus quotations and publisher URLs per request", "Reports the language and corpus version an answer came from", "Questions outside the collection come back marked, not invented", "Write merhaba@bedirsavasi.com for an institutional pilot"],
                      api_cta="Ask about a pilot"),
        corpus=dict(h2="The Badr collection", lead="Every text the assistant answers from is public, with its source.",
                    th_src="Source", th_desc="Detail",
                    rows=[("Qur'an (Arabic)", "Tanzil Uthmani text, via api.alquran.cloud"),
                          ("Qur'an (Turkish)", "Diyanet Vakfı meal (tr.vakfi)"),
                          ("Qur'an (English)", "Saheeh International (en.sahih)"),
                          ("Qur'an (German)", "Bubenheim & Elyas (de.bubenheim)"),
                          ("Hadith", "Sahih al-Bukhari and Sahih Muslim via fawazahmed0/hadith-api; numbering aligned with sunnah.com")],
                    note="Translation rights stay with their publishers. What we publish is our selection, four-language alignment and citation metadata. One file: /data/corpus.json"),
        roadmap=dict(h2="Roadmap, with status", lead="What shipped, what is running, what is only designed. We separate them.",
                     items=[("Shipped", "Cited question answering over the Battle of Badr collection: 41 Qur'an entries, 70 hadith entries, in four languages."),
                            ("In progress", "Expansion to the whole Qur'an and the six canonical hadith collections; topic-level retrieval."),
                            ("Designed, not run", "A published citation-accuracy evaluation separating quotation fidelity from citation support."),
                            ("Next", "A cited-answer API for Islamic schools and study platforms; a mobile app.")]),
        wait=dict(h2="Keep in touch", lead="We write when the collection grows and when the API opens.",
                  ph="your email", btn="Join the list", privacy="Your address is stored as a single row in Cloudflare and can be deleted by writing to merhaba@bedirsavasi.com. No marketing drip."),
        faq=dict(h2="Questions", items=[
            ("Do you issue rulings?", "No. Bedir AI is an information tool; ask it for a fatwa and it sends you to a qualified scholar."),
            ("Which model do you use?", "The product is built on the Claude API. When the Console account carries no credit balance, the demo runs on a labelled backup model stated above the answer; a backup answer is never presented as a Claude citation."),
            ("Can the answers be wrong?", "Yes. A citation makes it measurable that the quotation appears in the source; it does not guarantee the whole sentence is correct."),
            ("Do you store my data?", "There is no chat history. If you join the list, only your email address is stored."),
            ("Why only Badr?", "A collection is only trustworthy when it was built verifiably on a narrow subject. That work is ongoing.")]),
        legal="Bedir AI · Ankara, Türkiye · 2026 · operating name, not a registered legal entity · <a href=\"mailto:merhaba@bedirsavasi.com\">merhaba@bedirsavasi.com</a>",
        disclosure="You are talking to an AI assistant, not a person. Answers are generated from the cited sources and may contain errors.",
        fatwa_note="Bedir AI is an information tool and does not issue fatwas. For a binding religious ruling, consult a qualified scholar.",
        count_note="joined so far"),
    "de": dict(
        locale="de", dir_="ltr", title="Bedir AI • KI-Assistent für islamische Quellen mit Belegen",
        desc="Ein KI-Assistent für Fragen zu Koran und Hadith, der zu jeder Antwort die belegte Stelle und den Link zum Herausgeber zeigt. Aufbau auf der Anthropic-Claude-API.",
        nav=dict(ask="Frage", docs="API-Doku", product="Produkt", how="Funktionsweise", corpus="Korpus", api="Für Institutionen", company="Unternehmen", contact="Kontakt"),
        hero=dict(
            eyebrow="CLAUDE-API · ZITATE", h1a="Zitierte Antworten", h1b="auf Koran- und Hadith-Fragen.",
            sub="Ein Assistent und eine HTTP-API über einer kuratierten Sammlung. Jede Antwort öffnet die genaue Stelle samt Verlagslink. Prüfen ja, Editieren nein.",
            ex_label="AUFGEZEICHNETES BEISPIEL", ex_apilink="API-Anfrage und Antwort ansehen", ex_q="Welcher Vers erwähnt die Hilfe bei Badr?", ex_a="Koran 3:123 sagt, dass bei Badr Hilfe gesandt wurde.", ex_title="Koran 3:123 (Āl ʿImrān)", ex_pub="Tanzil · Bubenheim &amp; Elyas",
            cta_demo="Beispielauswertung ansehen", cta_api="API-Dokumentation",
            preview_label="BEISPIELFRAGE UND QUELLE", preview_q="Welche Sure beschreibt die Hilfe bei Badr?",
            preview_ans="Koran 3:123 berichtet, dass bei Badr geholfen wurde. [1]", preview_src="[1] Koran 3:123 · Quelle öffnen ↗"),
        proof=["41 Verse + 70 Hadithe, auf Badr beschränkt", "Abdeckung: ar · en · tr vollständig, de 41 von 111"],
        example=dict(h2="Einmal fragen, zweimal prüfen", lead="Jede nummerierte Markierung öffnet die belegte Stelle und den Link zum Herausgeber. Unten ein echter Datensatz, wörtlich zitiert.",
                     note="Ein Zitat garantiert nicht, dass die Antwort stimmt. Es garantiert, dass du nachsehen kannst."),
        how=dict(h2="Funktionsweise", lead="Eine überprüfbare Kette statt einer erfundenen Antwort.",
                 steps=[("Die Sammlung", "Korantext nach der Tanzil-Uthmani-Ausgabe; türkisch Diyanet Vakfı, englisch Saheeh International, deutsch Bubenheim & Elyas; Hadithe aus offenen Datensätzen von Bukhari und Muslim, Nummerierung wie auf sunnah.com."),
                        ("Als Dokumente an Claude", "Jeder Vers und Hadith geht als eigenes Dokument mit serverseitigen Zitaten an die Claude-API. Ein cache_control-Breakpoint lässt die Sammlung bei Wiederholungsfragen aus dem Prompt-Cache lesen."),
                        ("Eine zitierte Antwort", "Claude darf nur aus diesen Dokumenten antworten, in der Sprache der Frage, und muss sagen, wenn die Sammlung eine Frage nicht deckt."),
                        ("Das Zitat im Interface", "Die Oberfläche zeigt zu jedem Zitat den Text, den Titel der Quelle und den Link zu quran.com oder sunnah.com.")]),
        audience=dict(h2="Für wen", lead="Die erste Veröffentlichung ist auf die Schlacht von Badr begrenzt. Uns interessiert der Schritt von der Idee zum Beleg im Unterricht.",
                      cards=[("Lehrende", "Belegstellen für ein Thema finden und das Zitat im Kontext lesen — prüfen per Klick, nicht per Vertrauen."),
                             ("Lesende", "Natürlich fragen, sehen, worauf sich eine Antwort stützt, und dem Link folgen."),
                             ("Frühe Recherche", "Einstiegspunkt finden, Antwort, Zitat und Quelle zusammen prüfen, Fehler melden.")],
                      api_h3="Für Schulen und Lernplattformen", api_lead="Mit wachsender Sammlung öffnen wir eine API für Produkte, die zitierte Antworten brauchen.",
                      api_items=["Liefert Text plus Zitate und Herausgeber-URLs", "Nennt Sprache und Korpusversion einer Antwort", "Nicht abgedeckte Fragen werden markiert, nicht erfunden", "Für einen Pilothof: merhaba@bedirsavasi.com"],
                      api_cta="Pilothof anfragen"),
        corpus=dict(h2="Die Badr-Sammlung", lead="Jeder Text, aus dem geantwortet wird, ist mit Quelle öffentlich.",
                    th_src="Quelle", th_desc="Detail",
                    rows=[("Koran (Arabisch)", "Tanzil-Uthmani-Text über api.alquran.cloud"),
                          ("Koran (Türkisch)", "Diyanet-Vakfı-Meal (tr.vakfi)"),
                          ("Koran (Englisch)", "Saheeh International (en.sahih)"),
                          ("Koran (Deutsch)", "Bubenheim & Elyas (de.bubenheim)"),
                          ("Hadithe", "Sahih al-Bukhari und Sahih Muslim über fawazahmed0/hadith-api; Nummerierung nach sunnah.com")],
                    note="Übersetzungsrechte bleiben bei den Verlagen. Wir veröffentlichen Auswahl, Sprachalignment und Zitier-Metadaten. Eine Datei: /data/corpus.json"),
        roadmap=dict(h2="Roadmap mit Status", lead="Was fertig ist, was läuft, was nur entworfen wurde.",
                     items=[("Fertig", "Zitierte问答 über die Badr-Sammlung: 41 Koran-, 70 Haditheinträge, vier Sprachen."),
                            ("Läuft", "Ausweitung auf den ganzen Koran und die sechs kanonischen Hadithsammlungen; Themenabruf."),
                            ("Entworfen, nicht gelaufen", "Eine veröffentlichte Bewertung der Zitiergenauigkeit: Wörtlichkeit und Tragfähigkeit getrennt."),
                            ("Als Nächstes", "Eine zitierte Antwort-API für islamische Schulen und Lernplattformen; eine App.")]),
        wait=dict(h2="Bleib dran", lead="Wir schreiben, wenn die Sammlung wächst und die API öffnet.",
                  ph="deine E-Mail", btn="In die Liste", privacy="Die Adresse liegt als einzelne Zeile bei Cloudflare und ist über merhaba@bedirsavasi.com löschbar. Kein Werbemail."),
        faq=dict(h2="Fragen", items=[
            ("Erteilt ihr Fatwas?", "Nein. Bedir AI ist ein Informationswerkzeug und verweist für verbindliche Urteile an einen qualifizierten Gelehrten."),
            ("Welches Modell?", "Das Produkt baut auf der Claude-API. Ohne Guthaben im Console-Konto läuft die Demo mit einem gekennzeichneten Ausweichmodell über der Antwort; ein Ausweichsatz wird nie als Claude-Zitat ausgegeben."),
            ("Können Antworten falsch sein?", "Ja. Ein Zitat macht messbar, dass die Stelle in der Quelle vorkommt; es garantiert nicht die Richtigkeit des Ganzen."),
            ("Speichert ihr meine Daten?", "Kein Chatverlauf. In der Liste steht nur die E-Mail-Adresse."),
            ("Warum nur Badr?", "Eine Sammlung ist nur dann vertrauenswürdig, wenn sie an einem engen Gegenstand nachprüfbar aufgebaut wurde.")]),
        legal="Bedir AI · Ankara, Türkei · 2026 · Geschäftsname, keine eingetragene Gesellschaft · <a href=\"mailto:merhaba@bedirsavasi.com\">merhaba@bedirsavasi.com</a>",
        disclosure="Sie sprechen mit einem KI-Assistenten, nicht mit einer Person. Antworten werden aus den zitierten Quellen erzeugt und können Fehler enthalten.",
        fatwa_note="Bedir AI ist ein Informationswerkzeug und erteilt keine Fatwas. Für ein verbindliches religiöses Urteil wenden Sie sich an einen qualifizierten Gelehrten.",
        count_note="bisher dabei"),
    "ar": dict(
        locale="ar", dir_="rtl", title="Bedir AI • مساعد معرفي بالقرآن والحديث يُظهر مصادره",
        desc="مساعد بالذكاء الاصطناعي لأسئلة القرآن والحديث، يعرض الآية أو الحديث الذي يُبنى عليه الجواب مع رابط إلى الناشر. مبني على Claude API من Anthropic.",
        nav=dict(ask="اسأل", docs="وثائق API", product="المنتج", how="كيف يعمل", corpus="المجموعة", api="للمؤسسات", company="عن الشركة", contact="تواصل"),
        hero=dict(
            eyebrow="Claude API · اقتباس", h1a="إجابات موثَّقة بالمصدر", h1b="لأسئلة القرآن والحديث.",
            sub="مساعد أسئلة وأجوبة وواجهة HTTP فوق مجموعة مختارة. كل جواب يفتح الآية أو الحديث الذي استند إليه مع رابط الناشر. يمكنك المراجعة، لا التحرير.",
            ex_label="مثال مسجَّل", ex_apilink="انظر طلب API واستجابته", ex_q="أي آية تتحدث عن النصر في بدر؟", ex_a="القرآن 3:123 يذكر أن الله نصر المؤمنين في بدر.", ex_title="القرآن 3:123 (آل عمران)", ex_pub="تنزيل (الرسم العثماني)",
            cta_demo="مثال مسجَّل", cta_api="وثائق API",
            preview_label="مثال: سؤال ومصدر", preview_q="أي آية تتحدث عن النصر في بدر؟",
            preview_ans="القرآن ٣:١٢٣ يذكر أن النصر كان في بدر. [1]", preview_src="[1] القرآن ٣:١٢٣ · افتح المصدر ↗"),
        proof=["٤١ آية + ٧٠ حديثًا: مجموعة بدر", "التغطية: ar · en · tr كاملة، de ٤١/١١١"],
        example=dict(h2="اسأل مرة، ودقّق مرتين", lead="كل علامة رقمية تفتح النص المقتبس ورابط الناشر. أدناه سجلّ حقيقي منقول حرفيًّا من المجموعة.",
                     note="الاقتباس لا يضمن صحة الجواب، بل يضمن وجود شيء يمكنك مراجعته."),
        how=dict(h2="كيف يعمل", lead="مسار قابل للتفتيش بدل جواب مُختلَق.",
                 steps=[("المجموعة", "نص القرآن عن نسخة Tanzil العثماني؛ الترجمة التركية من ديانت والمه، والإنجليزية Saheeh International، والألمانية Bubenheim & Elyas؛ والأحاديث من مجموعات البخاري ومسلم المفتوحة بأرقام مطابقة لسنة.كوم."),
                        ("وثائق إلى Claude", "كل آية وحديث تُرسل كوثيقة مستقلة مع تفعيل الاقتباس من جهة الخادم، ويُوضع cache_control على الوثيقة الأخيرة لتقرأ المجموعة من التخزين المؤقت في الأسئلة المتكررة."),
                        ("جواب مُقتبَس", "يقتصر الجواب على هذه الوثائق، بلغة السؤال، وإن لم تغطِّ المجموعة سؤالًا صرحت بذلك بدل الرجوع إلى المعرفة المحفوظة."),
                        ("الاقتباس على الشاشة", "يعرض الواجهة نص الاقتباس وعنوان المصدر ورابط quran.com أو sunnah.com لكل مرجع.")]),
        audience=dict(h2="لمن هذا؟", lead="الإصدار الأول مقصور على غزوة بدر، والعمل الذي نهتم به هو وصول المعلّم إلى النص وتحققه في خطوة.",
                      cards=[("للمعلمين", "اعثر على آيات وأحاديث مناسبة للموضوع، ثم اقرأ الاقتباس في سياقه؛ تحقق بالنقر لا بالثقة."),
                             ("للقارئ المستقل", "اسأل بلغتك، وانظر على أي نص يقوم الجواب، واتبع الرابط إلى قراءة أوسع."),
                             ("للبدايات البحثية", "اعثر على نقطة بداية، وافحص الجواب والاقتباس والمصدر معًا، وأبلغ عن الخطأ.")],
                      api_h3="للمدارس ومنصات الدراسة", api_lead="مع توسع المجموعة سنفتح واجهة برمجية تُعيد إجابات مُقتبَسة للمنتجات التي تحتاجها.",
                      api_items=["تعيد النص مع الاقتباسات وروابط الناشرين", "تذكر اللغة وإصدار المجموعة التي جُيب منها", "الأسئلة خارج المجموعة تُعلَّم ولا تُولَّد", "للتجربة المؤسسية: merhaba@bedirsavasi.com"],
                      api_cta="اطلب تجربة مؤسسة"),
        corpus=dict(h2="مجموعة بدر", lead="كل نص نجيب منه منشور مع مصدره.",
                    th_src="المصدر", th_desc="التفصيل",
                    rows=[("القرآن (عربي)", "نص Tanzil العثماني عبر api.alquran.cloud"),
                          ("القرآن (تركي)", "ترجمة ديانت Vakfı (tr.vakfi)"),
                          ("القرآن (إنجليزي)", "Saheeh International (en.sahih)"),
                          ("القرآن (ألماني)", "Bubenheim & Elyas (de.bubenheim)"),
                          ("الحديث", "صحيح البخاري وصحيح مسلم عبر fawazahmed0/hadith-api؛ الأرقام مطابقة لسنة.كوم")],
                    note="حقوق التراجم لأصحابها. ما ننشره هو اختيارنا ومحاذااتنا بين أربع لغات وبيانات الاقتباس. ملف واحد: /data/corpus.json"),
        roadmap=dict(h2="خارطة الطريق بحالتها", lead="ما تم، وما يجري، وما صُمِّم فقط.",
                     items=[("صدر", "إجابات مُقتبَسة من مجموعة غزوة بدر: ٤١ آية و٧٠ حديثًا بأربع لغات."),
                            ("جارٍ", "التوسع إلى القرآن كله وكتب الحديث الستة؛ الاسترجاع بحسب الموضوع."),
                            ("صُمِّم ولم يُنفَّذ", "تقويم منشور لدقة الاقتباس يفيد بين ثبوت النص ودعمه للادعاء."),
                            ("قادم", "واجهة إجابات مُقتبَسة للمدارس الإسلامية ومنصات الدراسة؛ تطبيق جوّال.")]),
        wait=dict(h2="تابع التطورات", lead="نكتب إليك حين تكبر المجموعة وحين تفتح الواجهة البرمجية.",
                  ph="بريدك الإلكتروني", btn="انضم إلى القائمة", privacy="يُحفظ بريدك كسطر واحد لدى Cloudflare ويمكن حذفه بمراسلة merhaba@bedirsavasi.com. لا رسائل دعائية."),
        faq=dict(h2="أسئلة متكررة", items=[
            ("هل تُصدرون فتوى؟", "لا. Bedir AI أداة معرفية، وتحيل من يطلب حكمًا ملزمًا إلى عالم مؤهل."),
            ("أي نموذج تستخدمون؟", "المنتج مبني على Claude API. وحين لا يكون في حساب Console رصيد، يعمل العرض التوضيحي بنموذج احتياطي موسوم فوق الجواب، ولا يُقدَّم جوابه كاقتباس من Claude."),
            ("هل تحتمل الإجابات الخطأ؟", "نعم. الاقتباس يجعل من الممكن قياس ورود النص في مصدره، لكنه لا يضمن صحة الجملة كلها."),
            ("هل تحفظون بياناتي؟", "لا نحفظ سجل المحادثة. وفي القائمة لا يُحفظ سوى بريدك."),
            ("لماذا بدر وحدها؟", "لا تُبنى الثقة في مجموعة إلا إذا شُيِّدت على موضوع ضيق بشكل قابل للتحقق.")]),
        legal="Bedir AI · أنقرة، تركيا · ٢٠٢٦ · اسم تشغيلي وليس كيانًا مسجلًا · <a href=\"mailto:merhaba@bedirsavasi.com\">merhaba@bedirsavasi.com</a>",
        disclosure="أنت تتحدث مع مساعد ذكاء اصطناعي وليس مع شخص. تُولَّد الإجابات من المصادر المقتبسة وقد تحتوي على أخطاء.",
        fatwa_note="Bedir AI أداة معرفية ولا يُصدر فتاوى. للحكم الشرعي المُلزِم استشر عالمًا مؤهَّلًا.",
        count_note="انضم حتى الآن"),
}

TPL = """<!DOCTYPE html>
<html lang="{locale}" dir="{dir_}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link rel="canonical" href="{canonical}" />
  {alternates}
  <link rel="icon" type="image/png" href="/favicon.png" />
  <link rel="stylesheet" href="/assets/style-DgdjaNys.css" />
  <link rel="stylesheet" href="/assets/product.css" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="https://bedirsavasi.com/epic-badr.jpg" />
  <meta property="og:locale" content="{locale}" />
  <script type="application/ld+json">
  {jsonld}
  </script>
</head>
<body class="home">
  <nav class="navbar glass">
    <div class="container nav-content">
      <a class="brand" href="{root}"><img src="/favicon.png" alt="" width="22" height="22" />Bedir AI</a>
      <button class="mobile-menu-toggle" id="menuToggle" aria-label="Menu"></button>
      <div class="nav-links" id="navLinks">
        <a href="#ask" class="btn-ghost">{nav_ask}</a>
        <a href="#corpus" class="btn-ghost">{nav_corpus}</a>
        <a href="{legal_base}api/" class="btn-ghost">{nav_docs}</a>
        <a href="{legal_base}company/" class="btn-ghost">{nav_company}</a>
      </div>
      <div class="lang-switcher">
        <a href="/" class="lang-btn{tr_active}">TR</a>
        <a href="/en/" class="lang-btn{en_active}">EN</a>
        <a href="/de/" class="lang-btn{de_active}">DE</a>
        <a href="/ar/" class="lang-btn{ar_active}">AR</a>
      </div>
    </div>
  </nav>

  <main>
    <section class="hero-section product-hero" id="product">
      <div class="container hero-grid">
        <div class="hero-copy">
          <span class="badge">{eyebrow}</span>
          <h1 class="hero-title product-headline">{h1a}<br><em>{h1b}</em></h1>
          <p class="hero-sub">{sub}</p>
          <div class="cta-row">
            <a class="btn-solid" href="#recorded">{cta_demo}</a>
            <a class="btn-outline" href="{legal_base}api/">{cta_api}</a>
          </div>
          <ul class="proof-strip">{proof_items}</ul>
        </div>
        <div class="demo-box glass hero-demo" id="ask">
          <form id="demo-form" class="demo-form">
            <input type="text" name="q" maxlength="400" placeholder="{demo_placeholder}" aria-label="{demo_aria}" required />
            <button class="btn-solid" type="submit">{demo_btn}</button>
          </form>
          <div class="demo-examples">{chips}</div>
          <p class="demo-disclosure">{disclosure}</p>
          <div id="demo-out" class="demo-out" aria-live="polite"></div>
            <p class="demo-evidence"><span>POST /api/ask</span><span>model claude-haiku-4-5-20251001</span><span>provider claude</span></p>
            <div class="demo-answer demo-example-answer" id="demo-example">
              <span class="demo-example-label">{ex_label}</span>
              <p class="preview-question">{ex_q}</p>
              <p class="recorded-answer">{ex_a} <sup>[1]</sup></p>
              <p class="demo-source demo-source-example"><b>[1]</b> <a href="{ex_url}" target="_blank" rel="noopener">{ex_title}</a> <span class="src-publisher">· {ex_pub}</span></p>
              <blockquote class="demo-quote">{ex_quote}</blockquote>
              <p class="demo-example-link"><a href="{legal_base}api/">{ex_apilink}</a></p>
            </div>
          <p class="demo-note">{fatwa_note}</p>
        </div>
      </div>
    </section>

    <section class="section" id="recorded">
      <div class="container">
        <h2>{ex_h2}</h2>
        <p class="lead">{ex_lead}</p>
        <div class="recorded glass">
          <p class="preview-question">{rec_q}</p>
          <p class="recorded-answer">{rec_ans}</p>
          <div class="demo-sources">{rec_sources}</div>
          <p class="metrics-note">{ex_note}</p>
        </div>
      </div>
    </section>

    <section class="section" id="how">
      <div class="container">
        <h2>{how_h2}</h2>
        <p class="lead">{how_lead}</p>
        <div class="how-grid">{how_steps}</div>
      </div>
    </section>

    <section class="section" id="audience">
      <div class="container">
        <h2>{aud_h2}</h2>
        <p class="lead">{aud_lead}</p>
        <div class="feature-grid">{aud_cards}</div>
        <div class="cta-box glass" id="institutions">
          <h3>{api_h3}</h3>
          <p>{api_lead}</p>
          <ul class="api-list">{api_items}</ul>
          <a class="btn-solid" href="mailto:merhaba@bedirsavasi.com?subject=Bedir%20AI%20pilot">{api_cta}</a>
        </div>
      </div>
    </section>

    <section class="section" id="corpus">
      <div class="container">
        <h2>{corpus_h2}</h2>
        <p class="lead">{corpus_lead}</p>
        <table class="fact-table">
          <tr><th scope="col">{th_src}</th><th scope="col">{th_desc}</th></tr>
          {corpus_rows}
        </table>
        <p class="metrics-note">{corpus_note} · <a href="/data/corpus.json">/data/corpus.json</a> · <a href="{github}">GitHub</a></p>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2>{road_h2}</h2>
        <p class="lead">{road_lead}</p>
        <div class="roadmap">{road_items}</div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2>{faq_h2}</h2>
        <div class="faq">{faq_items}</div>
      </div>
    </section>

    <section class="section">
      <div class="container cta-box glass">
        <h2>{wait_h2}</h2>
        <p>{wait_lead}</p>
        <form id="waitlist-form" class="waitlist-form">
          <input type="email" name="email" placeholder="{wait_ph}" aria-label="{wait_ph}" required />
          <button class="btn-solid" type="submit">{wait_btn}</button>
        </form>
        <p class="waitlist-status" id="waitlist-status" aria-live="polite"></p>
        <p class="metrics-note">{wait_privacy}</p>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="container">
      <p class="footer-legal">{legal} · <a href="{legal_base}company/">{nav_company}</a> · <a href="{github}">GitHub</a> · <a href="https://www.linkedin.com/in/mevlanayalcin/">LinkedIn</a> · <a href="{legal_base}privacy/">Privacy</a> · <a href="{legal_base}terms/">Terms</a></p>
      <div class="library-list">{library}</div>
    </div>
  </footer>
  <script src="/assets/nav.js" defer></script>
  <script src="/assets/demo.js" defer></script>
  <script src="/assets/waitlist.js" defer></script>
</body>
</html>
"""

RECORDED = {
    "tr": ("Bedir'de Ebû Cehil'i kim öldürdü?",
           "Ebû Cehil'i, Bedir günü Afra oğulları yaralamış; Abdullah b. Mesud onu bu hâlde bulup üzerine dayanmıştır.",
           "Buhârî 3963", "https://sunnah.com/bukhari:3963", "kaynağı aç ↗",
           "Narrated Anas: On the day of Badr, the Prophet (ﷺ) said, \"Who will go and see what has happened to Abu Jahl?\" Ibn Mas`ud went and found that the two sons of 'Afra had struck him fatally."),
    "en": ("Who killed Abu Jahl at Badr?",
           "On the day of Badr the Prophet asked who would see what had become of Abu Jahl; Ibn Mas'ud found him struck fatally by the two sons of 'Afra and finished him.",
           "Sahih al-Bukhari 3963", "https://sunnah.com/bukhari:3963", "open the source ↗",
           "Narrated Anas: On the day of Badr, the Prophet (ﷺ) said, \"Who will go and see what has happened to Abu Jahl?\" Ibn Mas`ud went and found that the two sons of 'Afra had struck him fatally."),
    "de": ("Wer tötete Abu Dschahl bei Badr?",
           "Am Tag von Badr fragte der Prophet, wer nachsehen solle, was mit Abu Dschahl geschehen sei; Ibn Mas'ud fand ihn von den beiden Söhnen der 'Afra tödlich getroffen.",
           "Sahih al-Bukhari 3963", "https://sunnah.com/bukhari:3963", "Quelle öffnen ↗",
           "Narrated Anas: On the day of Badr, the Prophet (ﷺ) said, \"Who will go and see what has happened to Abu Jahl?\" Ibn Mas`ud went and found that the two sons of 'Afra had struck him fatally."),
    "ar": ("من قتل أبا جهل في بدر؟",
           "في يوم بدر سأل النبي عمّن ينظر ما فعل أبو جهل، فوجده ابن مسعود قد أصابه ابنا عفراء بجراح قاتلة.",
           "صحيح البخاري ٣٩٦٣", "https://sunnah.com/bukhari:3963", "افتح المصدر ↗",
           "Narrated Anas: On the day of Badr, the Prophet (ﷺ) said, \"Who will go and see what has happened to Abu Jahl?\" Ibn Mas`ud went and found that the two sons of 'Afra had struck him fatally."),
}

CHIP_QS = {
    "tr": ["Bedir'de yardım hangi ayette geçiyor?", "Bedir'e kaç kişiyle gidildi?", "Bedir esirlerine nasıl muamele edildi?"],
    "en": ["How does the Qur'an describe the help at Badr?", "How many Muslims fought at Badr?", "What happened to Abu Jahl?"],
    "de": ["Wie beschreibt der Koran die Hilfe bei Badr?", "Wie viele Muslime kämpften bei Badr?", "Was geschah mit Abu Dschahl?"],
    "ar": ["كيف يصف القرآن النصر في بدر؟", "كم عدد المسلمين في بدر؟", "من قتل أبا جهل؟"],
}
DEMO_UI = {
    "tr": dict(ph="Örn. Meleklerin yardımı hangi âyette?", aria="Sorunuz", btn="Sor"),
    "en": dict(ph="e.g. Where does it say the angels helped?", aria="Your question", btn="Ask"),
    "de": dict(ph="z.B. Wo steht von der Hilfe der Engel?", aria="Ihre Frage", btn="Frage"),
    "ar": dict(ph="مثال: أين وردت مساعدة الملائكة؟", aria="سؤالك", btn="اسأل"),
}
LIBRARY = {
    "tr": "Koleksiyon: <a href=\"/ayet-i-kerimeler/\">Âyetler</a> · <a href=\"/hadis-i-serifler/\">Hadisler</a> · <a href=\"/ashabi-bedir/\">Bedir Ashabı</a> · <a href=\"/savasin-hikayesi/\">Savaşın hikâyesi</a> · <a href=\"/gazve-nedir/\">Gazve nedir</a> · <a href=\"/gunumuzde-bedir/\">Bedir bugün</a>",
    "en": "Collection: <a href=\"/en/ayet-i-kerimeler/\">Verses</a> · <a href=\"/en/hadis-i-serifler/\">Hadith</a> · <a href=\"/en/ashabi-bedir/\">Companions of Badr</a> · <a href=\"/en/savasin-hikayesi/\">The story of Badr</a> · <a href=\"/en/gunumuzde-bedir/\">Badr today</a>",
    "de": "Sammlung: <a href=\"/de/ayet-i-kerimeler/\">Verse</a> · <a href=\"/de/hadis-i-serifler/\">Hadithe</a> · <a href=\"/de/savasin-hikayesi/\">Die Schlacht von Badr</a>",
    "ar": "المجموعة: <a href=\"/ar/ayet-i-kerimeler/\">الآيات</a> · <a href=\"/ar/hadis-i-serifler/\">الأحاديث</a> · <a href=\"/ar/savasin-hikayesi/\">وقعة بدر</a>",
}

KOK = pathlib.Path(__file__).resolve().parent.parent

KAYIT_DOSYASI = KOK / "data" / "recorded_examples.json"
# The examples on the homepage are captured responses from the running endpoint, not
# hand-written copy: a sample nobody can reproduce is how the hero and the API docs ended
# up quoting different verses for the same question.
KAYITLAR = json.loads(KAYIT_DOSYASI.read_text(encoding="utf-8")) if KAYIT_DOSYASI.exists() else {}
# The worked example further down the page is a second captured response, so it does not
# repeat the hero. It keeps every answer block and every citation the endpoint returned.
CALISMA_DOSYASI = KOK / "data" / "recorded_worked.json"
CALISMALAR = json.loads(CALISMA_DOSYASI.read_text(encoding="utf-8")) if CALISMA_DOSYASI.exists() else {}


def kayit_html(kayit, ac):
    """Returns (question, answer, sources) HTML for a captured /api/ask response."""
    kaynaklar, anahtarlar, parcalar = [], [], []
    for blok in kayit.get("answer") or []:
        isaretler = ""
        for atif in blok.get("cites") or []:
            anahtar = (atif.get("id"), atif.get("quote"))
            if anahtar not in anahtarlar:
                anahtarlar.append(anahtar)
                kaynaklar.append(atif)
            isaretler += " <sup>[%d]</sup>" % (anahtarlar.index(anahtar) + 1)
        parcalar.append(escape(blok.get("text") or "", quote=False) + isaretler)
    cevap = " ".join("".join(parcalar).split())
    kaynak = "".join(
        '<div class="demo-source" id="src-demo-%d"><b>[%d] %s</b> · <a href="%s" target="_blank" rel="noopener">%s</a>'
        "<blockquote>%s</blockquote></div>"
        % (i + 1, i + 1, escape(k.get("title") or ""), escape(k.get("url") or ""), ac,
           escape(" ".join((k.get("quote") or "").split()), quote=False))
        for i, k in enumerate(kaynaklar))
    return escape(kayit.get("q") or "", quote=False), cevap, kaynak


def korpus_aliintisi(lang, kim="Q3:123", uzunluk=230):
    """Hero ornegindeki alinti, sunulan korpusun kendisinden okunur; elle yazilmaz."""
    veri = json.loads((KOK / "data" / "corpus.json").read_text(encoding="utf-8"))
    for kayit in veri["items"]:
        if kayit.get("id") == kim:
            metin = (kayit.get("text") or {}).get(lang) or (kayit.get("text") or {}).get("en") or ""
            metin = " ".join(metin.split())
            return metin if len(metin) <= uzunluk else metin[:uzunluk].rsplit(" ", 1)[0] + " …"
    return ""

OUT = {"tr": "site/index.html", "en": "site/en/index.html", "de": "site/de/index.html", "ar": "site/ar/index.html"}
BASE = {"tr": "/", "en": "/en/", "de": "/de/", "ar": "/ar/"}


def jsonld_for(lang, t):
    return (
        '{"@context":"https://schema.org","@graph":['
        '{"@type":"Organization","@id":"https://bedirsavasi.com/#org","name":"Bedir AI",'
        '"url":"https://bedirsavasi.com/","email":"merhaba@bedirsavasi.com","logo":"https://bedirsavasi.com/favicon.png",'
        '"foundingDate":"2026-03-08","founder":{"@type":"Person","name":"Mevlana Yalçın","url":"%s"},"numberOfEmployees":{"@type":"QuantitativeValue","value":1},"contactPoint":{"@type":"ContactPoint","contactType":"customer support","email":"merhaba@bedirsavasi.com","availableLanguage":["tr","en","de","ar"]},"codeRepository":"%s",'
        '"sameAs":["%s","%s"],'
        '"description":%s,'
        '"address":{"@type":"PostalAddress","addressLocality":"Ankara","addressCountry":"TR"}},'
        '{"@type":"WebApplication","name":"Bedir AI","url":"https://bedirsavasi.com/%s/","applicationCategory":"EducationalApplication",'
        '"operatingSystem":"Web","inLanguage":["tr","en","de","ar"],"publisher":{"@id":"https://bedirsavasi.com/#org"},'
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"description":%s}]}'
        % (LI, GITHUB, GITHUB, LI, json.dumps(t["desc"], ensure_ascii=False), lang, json.dumps(t["desc"], ensure_ascii=False))
    )


def build(lang):
    t = T[lang]
    rec_q, rec_ans, rec_title, rec_url, rec_link, rec_quote = RECORDED[lang]
    kayit = KAYITLAR.get(lang) or {}
    if kayit:
        atif = (kayit.get("cites") or [{}])[0]
        rec_q = kayit.get("q") or rec_q
        rec_ans = " ".join((kayit.get("text") or "").split()) or rec_ans
        rec_title = atif.get("title") or rec_title
        rec_url = atif.get("url") or rec_url
        rec_link = (atif.get("title") or rec_title) + " ↗"
        rec_quote = " ".join((atif.get("quote") or "").split()) or rec_quote
    if lang in CALISMALAR:
        calisma_q, calisma_ans, calisma_src = kayit_html(CALISMALAR[lang], RECORDED[lang][4])
    else:
        calisma_q, calisma_ans = rec_q, rec_ans
        calisma_src = ('<div class="demo-source" id="src-demo-1"><b>[1] %s</b> · <a href="%s" target="_blank" rel="noopener">%s</a>'
                       "<blockquote>%s</blockquote></div>" % (rec_title, rec_url, rec_link, rec_quote))
    alternates = "\n  ".join(
        '<link rel="alternate" hreflang="%s" href="https://bedirsavasi.com%s" />' % (l, "/" if l == "tr" else "/%s/" % l)
        for l in ("tr", "en", "de", "ar")
    ) + '\n  <link rel="alternate" hreflang="x-default" href="https://bedirsavasi.com/en/" />'
    ui = DEMO_UI[lang]
    return TPL.format(
        locale=t["locale"], dir_=t["dir_"], title=t["title"], desc=t["desc"],
        canonical="https://bedirsavasi.com" + ("/" if lang == "tr" else "/%s/" % lang),
        alternates=alternates, jsonld=jsonld_for(lang, t),
        root=BASE[lang], base=BASE[lang], github=GITHUB,
        nav_ask=t["nav"]["ask"], nav_docs=t["nav"]["docs"], nav_product=t["nav"]["product"], nav_how=t["nav"]["how"], nav_corpus=t["nav"]["corpus"],
        nav_api=t["nav"]["api"], nav_company=t["nav"]["company"], nav_contact=t["nav"]["contact"],
        tr_active=" active-link" if lang == "tr" else "",  en_active=" active-link" if lang == "en" else "", 
        de_active=" active-link" if lang == "de" else "",  ar_active=" active-link" if lang == "ar" else "", 
        eyebrow=t["hero"]["eyebrow"], h1a=t["hero"]["h1a"], h1b=t["hero"]["h1b"], sub=t["hero"]["sub"],
        cta_demo=t["hero"]["cta_demo"], cta_api=t["hero"]["cta_api"],
        proof_items="".join("<li>%s</li>" % p for p in t["proof"]),
        demo_placeholder=ui["ph"], demo_aria=ui["aria"], demo_btn=ui["btn"],
        chips="".join('<button type="button">%s</button>' % q for q in CHIP_QS[lang]),
        disclosure=t["disclosure"], fatwa_note=t["fatwa_note"],
        ex_label=t["hero"]["ex_label"], ex_q=rec_q, ex_a=rec_ans,
        legal_base=(BASE[lang] if lang in ("tr", "en") else "/en/"),
        ex_title=rec_title, ex_pub=t["hero"]["ex_pub"], ex_url=rec_url,
        ex_quote=rec_quote or korpus_aliintisi(lang), ex_apilink=t["hero"]["ex_apilink"],
        ex_h2=t["example"]["h2"], ex_lead=t["example"]["lead"], ex_note=t["example"]["note"],
        rec_q=calisma_q, rec_ans=calisma_ans, rec_sources=calisma_src,
        how_h2=t["how"]["h2"], how_lead=t["how"]["lead"],
        how_steps="".join(
            '<div class="how-card glass"><span class="how-num">%d</span><h3>%s</h3><p>%s</p></div>' % (i + 1, a, b)
            for i, (a, b) in enumerate(t["how"]["steps"])),
        aud_h2=t["audience"]["h2"], aud_lead=t["audience"]["lead"],
        aud_cards="".join('<article class="feature-card glass"><h3>%s</h3><p>%s</p></article>' % (a, b) for a, b in t["audience"]["cards"]),
        api_h3=t["audience"]["api_h3"], api_lead=t["audience"]["api_lead"],
        api_items="".join("<li>%s</li>" % s for s in t["audience"]["api_items"]), api_cta=t["audience"]["api_cta"],
        corpus_h2=t["corpus"]["h2"], corpus_lead=t["corpus"]["lead"], th_src=t["corpus"]["th_src"], th_desc=t["corpus"]["th_desc"],
        corpus_rows="".join("<tr><th scope=\"row\">%s</th><td>%s</td></tr>" % (a, b) for a, b in t["corpus"]["rows"]),
        corpus_note=t["corpus"]["note"],
        road_h2=t["roadmap"]["h2"], road_lead=t["roadmap"]["lead"],
        road_items="".join('<div class="road-item"><span class="road-label">%s</span><p>%s</p></div>' % (a, b) for a, b in t["roadmap"]["items"]),
        faq_h2=t["faq"]["h2"], faq_items="".join('<details class="faq-item" open><summary>%s</summary><p>%s</p></details>' % (q, a) for q, a in t["faq"]["items"]),
        wait_h2=t["wait"]["h2"], wait_lead=t["wait"]["lead"], wait_ph=t["wait"]["ph"], wait_btn=t["wait"]["btn"],
        wait_privacy=t["wait"]["privacy"], legal=t["legal"], library=LIBRARY[lang],
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = []
    for lang, rel in OUT.items():
        html = build(lang)
        p = REPO / rel
        if args.check:
            cur = p.read_text(encoding="utf-8") if p.exists() else ""
            if hashlib.sha256(cur.encode()).hexdigest() != hashlib.sha256(html.encode()).hexdigest():
                bad.append(rel)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        print("%-22s %5d satir" % (rel, html.count("\n") + 1))
    if args.check and bad:
        print("elde uretilmemis:", ", ".join(bad)); sys.exit(1)


if __name__ == "__main__":
    main()
