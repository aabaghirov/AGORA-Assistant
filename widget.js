/* Agora chat widget. Embed anywhere (WordPress "Custom HTML"/footer):
   <script src="https://YOUR-API-HOST/widget.js" defer></script> */
(() => {
  const API = new URL(document.currentScript.src).origin;
  const S = (() => { try { return sessionStorage } catch { return {} } })();
  const sid = S.sid || (S.sid = Math.random().toString(36).slice(2));
  const L = {
    en: { title: "Agora Assistant", sub: "Ask about programs and services", ph: "Type your question…", send: "Send",
      hi: "Hi! I can answer questions about Agora's programs, help you find the right one, or book a free initial consultation.",
      chips: ["Which program is for me?", "What do you do for essays?", "Book a consultation"],
      book: "Book a consultation", consent: "We will use your details only to contact you about a consultation. If the student is under 18, a parent or guardian should confirm.",
      name: "Your name", contact: "Phone or email", time: "Preferred time (e.g. weekdays after 5pm)", student: "I'm a student", parent: "I'm a parent",
      agree: "I agree to be contacted", submit: "Send to Agora team", done: "Thanks! The Agora team will contact you soon.", err: "Something went wrong. Please try again or call Agora." },
    az: { title: "Agora Assistenti", sub: "Proqramlar və xidmətlər barədə soruşun", ph: "Sualınızı yazın…", send: "Göndər",
      hi: "Salam! Agora proqramları barədə suallarınızı cavablandıra, sizə uyğun proqramı tapmağa və ilkin konsultasiya təyin etməyə kömək edə bilərəm.",
      chips: ["Mənə hansı proqram uyğundur?", "Esse üçün nə edirsiniz?", "Konsultasiyaya yazıl"],
      book: "Konsultasiyaya yazıl", consent: "Məlumatlarınız yalnız konsultasiya üçün sizinlə əlaqə saxlamaq məqsədilə istifadə olunacaq. Şagird 18 yaşdan kiçikdirsə, valideyn razılığı lazımdır.",
      name: "Adınız", contact: "Telefon və ya e-poçt", time: "Əlverişli vaxt", student: "Şagirdəm", parent: "Valideynəm",
      agree: "Əlaqə saxlanmasına razıyam", submit: "Agora komandasına göndər", done: "Təşəkkürlər! Agora komandası tezliklə sizinlə əlaqə saxlayacaq.", err: "Xəta baş verdi. Yenidən cəhd edin və ya Agora ilə zəng vasitəsilə əlaqə saxlayın." } };
  let lang = (document.documentElement.lang || "en").startsWith("az") ? "az" : "en", msgs = [], open = false;
  const css = document.createElement("style");
  css.textContent = `.ag{font:15px/1.45 system-ui,sans-serif;position:fixed;right:20px;bottom:20px;z-index:99999}
  .ag *{box-sizing:border-box}.ag-fab{width:58px;height:58px;border-radius:50%;border:0;background:#B4233C;color:#fff;font-size:26px;cursor:pointer;box-shadow:0 6px 20px #0003}
  .ag-p{display:none;position:absolute;right:0;bottom:70px;width:370px;max-width:calc(100vw - 32px);height:540px;max-height:calc(100vh - 110px);background:#fff;color:#12343B;border-radius:16px;box-shadow:0 12px 40px #0004;flex-direction:column;overflow:hidden}
  .ag-p.on{display:flex}.ag-h{background:#12343B;color:#fff;padding:12px 14px;display:flex;justify-content:space-between;align-items:center}
  .ag-h small{display:block;opacity:.7}.ag-h button{background:#ffffff22;color:#fff;border:0;border-radius:8px;padding:4px 10px;cursor:pointer}
  .ag-m{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#F3F6F5}
  .ag-b{max-width:85%;padding:9px 12px;border-radius:14px;white-space:pre-wrap}.ag-b.bot{background:#fff;align-self:flex-start}.ag-b.me{background:#12343B;color:#fff;align-self:flex-end}
  .ag-c{display:flex;flex-wrap:wrap;gap:6px}.ag-c button,.ag-bk{border:1px solid #12343B;background:#fff;color:#12343B;border-radius:999px;padding:5px 11px;cursor:pointer;font:inherit}
  .ag-bk{border-color:#B4233C;color:#B4233C;margin:0 12px 8px;align-self:flex-start}
  .ag-i{display:flex;gap:6px;padding:10px;border-top:1px solid #0001}.ag-i input,.ag-f input,.ag-f select{flex:1;border:1px solid #0003;border-radius:10px;padding:9px;font:inherit;width:100%}
  .ag-i button,.ag-f button{background:#B4233C;color:#fff;border:0;border-radius:10px;padding:9px 14px;cursor:pointer;font:inherit}
  .ag-f{padding:12px;display:flex;flex-direction:column;gap:8px;overflow:auto}.ag-f p{margin:0;font-size:13px;opacity:.8}.ag-f label{font-size:13px}`;
  document.head.append(css);
  const el = (h) => { const d = document.createElement("div"); d.innerHTML = h; return d.firstElementChild };
  const root = el(`<div class="ag"><div class="ag-p" role="dialog" aria-label="Agora Assistant"><div class="ag-h"><div><b></b><small></small></div><button aria-label="Language"></button></div><div class="ag-m" aria-live="polite"></div><button class="ag-bk"></button><div class="ag-i"><input><button></button></div></div><button class="ag-fab" aria-label="Chat">💬</button></div>`);
  document.body.append(root);
  const $ = (s) => root.querySelector(s), P = $(".ag-p"), M = $(".ag-m"), inp = $(".ag-i input");
  const add = (t, w) => { const b = el(`<div class="ag-b ${w}"></div>`); b.textContent = t; M.append(b); M.scrollTop = M.scrollHeight; return b };
  function chips() { const c = el(`<div class="ag-c"></div>`); L[lang].chips.forEach((t, i) => { const b = document.createElement("button"); b.textContent = t; b.onclick = () => { c.remove(); i === 2 ? form() : say(t) }; c.append(b) }); M.append(c) }
  function ui() { const t = L[lang]; $(".ag-h b").textContent = t.title; $(".ag-h small").textContent = t.sub; $(".ag-h button").textContent = lang === "en" ? "AZ" : "EN";
    $(".ag-bk").textContent = t.book; inp.placeholder = t.ph; $(".ag-i button").textContent = t.send }
  function reset() { M.innerHTML = ""; msgs = []; add(L[lang].hi, "bot"); chips(); ui() }
  async function say(text) {
    add(text, "me"); msgs.push({ role: "user", content: text }); const w = add("…", "bot");
    try {
      const r = await (await fetch(API + "/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session: sid, lang, messages: msgs }) })).json();
      w.textContent = r.reply; msgs.push({ role: "assistant", content: r.reply });
      if (r.intent === "book" || r.intent === "handoff") form();
    } catch { w.textContent = L[lang].err }
  }
  function form() {
    if (M.querySelector(".ag-f")) return; const t = L[lang];
    const f = el(`<div class="ag-f"><p>${t.consent}</p><input name="n" placeholder="${t.name}"><input name="c" placeholder="${t.contact}"><input name="t" placeholder="${t.time}">
      <select name="r"><option value="student">${t.student}</option><option value="parent">${t.parent}</option></select>
      <label><input type="checkbox" name="g" style="width:auto"> ${t.agree}</label><button>${t.submit}</button></div>`);
    M.append(f); M.scrollTop = M.scrollHeight;
    f.querySelector("button").onclick = async () => {
      const g = (n) => f.querySelector(`[name=${n}]`);
      if (!g("n").value || !g("c").value || !g("g").checked) return;
      try {
        const r = await fetch(API + "/api/lead", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session: sid, name: g("n").value, contact: g("c").value, time: g("t").value, role: g("r").value, lang, consent: true, transcript: msgs }) });
        if (!r.ok) throw 0; f.remove(); add(t.done, "bot");
      } catch { add(t.err, "bot") }
    };
  }
  $(".ag-fab").onclick = () => { open = !open; P.classList.toggle("on", open); if (open && !M.children.length) reset() };
  $(".ag-h button").onclick = () => { lang = lang === "en" ? "az" : "en"; reset() };
  $(".ag-bk").onclick = form;
  const go = () => { const v = inp.value.trim(); if (v) { inp.value = ""; say(v) } };
  $(".ag-i button").onclick = go; inp.onkeydown = (e) => e.key === "Enter" && go();
})();
