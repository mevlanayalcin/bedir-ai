// Live demo: posts the question to /api/ask and renders the answer with its citations.
(() => {
  const lang = document.documentElement.lang || "en";
  const T = {
    tr: { thinking: "Kaynaklar taranıyor…", sources: "Kaynaklar", none: "Bu cevap kaynak göstermedi; demo korpusu bu soruyu kapsamıyor olabilir.", busy: "Şu an çok fazla istek var, lütfen biraz sonra tekrar deneyin.", error: "Bir hata oluştu, lütfen tekrar deneyin.", refused: "Bu soru yanıtlanamadı.", bad: "Lütfen 400 karakteri geçmeyen bir soru yazın.", open: "Kaynağı aç" },
    en: { thinking: "Searching the sources…", sources: "Sources", none: "This answer cited no source; the demo corpus may not cover this question.", busy: "Too many requests right now, please try again shortly.", error: "Something went wrong, please try again.", refused: "This question could not be answered.", bad: "Please enter a question of up to 400 characters.", open: "Open source" },
    de: { thinking: "Quellen werden durchsucht…", sources: "Quellen", none: "Diese Antwort nennt keine Quelle; das Demo-Korpus deckt die Frage womöglich nicht ab.", busy: "Gerade gibt es zu viele Anfragen, bitte versuchen Sie es gleich noch einmal.", error: "Es ist ein Fehler aufgetreten, bitte erneut versuchen.", refused: "Diese Frage konnte nicht beantwortet werden.", bad: "Bitte geben Sie eine Frage mit höchstens 400 Zeichen ein.", open: "Quelle öffnen" },
    ar: { thinking: "جارٍ البحث في المصادر…", sources: "المصادر", none: "لم تستشهد هذه الإجابة بأي مصدر؛ قد لا تغطي مدوّنة العرض هذا السؤال.", busy: "الطلبات كثيرة الآن، يرجى المحاولة بعد قليل.", error: "حدث خطأ، يرجى المحاولة مرة أخرى.", refused: "تعذّرت الإجابة عن هذا السؤال.", bad: "يرجى كتابة سؤال لا يتجاوز 400 حرف.", open: "فتح المصدر" },
  }[lang] || {};

  const form = document.getElementById("demo-form");
  if (!form) return;
  const input = form.querySelector("input");
  const button = form.querySelector("button");
  const out = document.getElementById("demo-out");

  const el = (tag, props = {}, ...children) => {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
  };

  function render(answer) {
    out.replaceChildren();
    const sources = [];
    const indexOf = (cite) => {
      let i = sources.findIndex((s) => s.id === cite.id && s.quote === cite.quote);
      if (i === -1) i = sources.push(cite) - 1;
      return i + 1;
    };
    const p = el("p");
    for (const part of answer) {
      p.append(part.text);
      for (const cite of part.cites) {
        const n = indexOf(cite);
        p.append(el("sup", {}, el("a", { href: `#src-${n}`, textContent: `[${n}]` })));
      }
    }
    out.append(p);
    if (!sources.length) {
      out.append(el("p", { className: "status", textContent: T.none }));
      return;
    }
    const list = el("div", { className: "demo-sources" });
    sources.forEach((s, i) => {
      list.append(
        el("div", { className: "demo-source", id: `src-${i + 1}` },
          el("b", { textContent: `[${i + 1}] ${s.title}` }), " · ",
          el("a", { href: s.url, target: "_blank", rel: "noopener", textContent: T.open }),
          el("blockquote", { textContent: s.quote.trim() })));
    });
    out.append(el("h3", { textContent: T.sources, style: "margin-top:1rem;font-size:1rem;color:#ffebcc" }), list);
  }

  async function ask(q) {
    q = q.trim();
    if (!q || q.length > 400) {
      out.replaceChildren(el("p", { className: "status", textContent: T.bad }));
      return;
    }
    button.disabled = true;
    out.replaceChildren(el("p", { className: "status", textContent: T.thinking }));
    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ q, lang }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 429 || data.error === "busy") throw new Error(T.busy);
      if (data.error === "refused") throw new Error(T.refused);
      if (!res.ok || !data.answer) throw new Error(T.error);
      render(data.answer);
    } catch (err) {
      out.replaceChildren(el("p", { className: "status", textContent: err.message || T.error }));
    } finally {
      button.disabled = false;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    ask(input.value);
  });
  document.querySelectorAll(".demo-examples button").forEach((b) =>
    b.addEventListener("click", () => {
      input.value = b.textContent;
      ask(b.textContent);
    }));
})();
