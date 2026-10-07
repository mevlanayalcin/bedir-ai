// Waitlist form. Replaces the Netlify Forms attribute, which stopped working when the site
// moved to Cloudflare: submissions were accepted by a suspended project and went nowhere.
(() => {
  const form = document.getElementById("waitlist-form");
  if (!form) return;
  const out = document.getElementById("waitlist-status");
  const lang = document.documentElement.lang || "en";
  const T = {
    tr: { sent: "Eklendin, teşekkürler.", dup: "Zaten listedesin.", bad: "Geçerli bir e-posta gir.", err: "Şu an kaydedemedik, birazdan tekrar dene." },
    en: { sent: "You're on the list, thank you.", dup: "You are already on the list.", bad: "Enter a valid email.", err: "Could not save just now, try again shortly." },
    de: { sent: "Du bist dabei, danke.", dup: "Du stehst schon auf der Liste.", bad: "Gültige E-Mail eingeben.", err: "Gerade nicht gespeichert, bitte gleich erneut." },
    ar: { sent: "أضفت، شكراً.", dup: "أنت في القائمة بالفعل.", bad: "أدخل بريداً صحيحاً.", err: "لم نتمكن من الحفظ الآن، أعد المحاولة." },
  }[lang] || {};

  async function post(email) {
    const res = await fetch("/api/waitlist", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, lang, source: "homepage" }),
    });
    return { status: res.status, data: await res.json().catch(() => ({})) };
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = (form.querySelector("input[name=email]").value || "").trim();
    if (!/^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(email)) {
      out.textContent = T.bad || "Invalid email";
      return;
    }
    const btn = form.querySelector("button");
    btn.disabled = true;
    try {
      const { data } = await post(email);
      out.textContent = data.created ? (T.sent || "Added") : (data.duplicate ? (T.dup || "Already on the list") : (T.err || "Failed"));
      if (data.created) form.reset();
    } catch {
      out.textContent = T.err || "Failed";
    } finally {
      btn.disabled = false;
    }
  });

  // Show how many people joined, straight from the same store.
  fetch("/api/waitlist")
    .then((r) => (r.ok ? r.json() : {}))
    .then((d) => {
      if (d && typeof d.count === "number") out.textContent = d.count + " " + (COUNT_LABEL[lang] || COUNT_LABEL.en);
    })
    .catch(() => {});

  const COUNT_LABEL = {
    tr: "kişi şu ana kadar katıldı",
    en: "people have joined so far",
    de: "Personen sind bisher dabei",
    ar: "انضم حتى الآن",
  };
})();
