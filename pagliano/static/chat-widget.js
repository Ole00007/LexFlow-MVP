/**
 * Pagliano Law Firm — Chat Widget ("Alessia")
 * Standalone: no external dependencies, no API calls.
 * Loaded via <script src="/static/chat-widget.js"></script>
 */
(function () {
  "use strict";

  /* ── State ─────────────────────────────────────────────── */
  var state = {
    open: false,
    step: "greeting",
    flow: {}, // accumulates user answers per conversation
  };

  /* ── DOM refs (lazy) ───────────────────────────────────── */
  var btn, panel, header, messages, input, sendBtn, closeBtn;

  function getEls() {
    if (btn) return;
    btn = document.getElementById("chat-toggle-btn");
    panel = document.getElementById("chat-panel");
    header = document.getElementById("chat-panel-header");
    messages = document.getElementById("chat-messages");
    input = document.getElementById("chat-input");
    sendBtn = document.getElementById("chat-send-btn");
    closeBtn = document.getElementById("chat-close-btn");
  }

  /* ── Init ──────────────────────────────────────────────── */
  function init() {
    getEls();
    if (!btn) return;

    // Place floating button before panel
    if (panel) panel.style.display = "none";

    btn.addEventListener("click", toggleChat);
    if (closeBtn) closeBtn.addEventListener("click", toggleChat);
    if (sendBtn) sendBtn.addEventListener("click", handleSend);
    if (input) {
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") handleSend();
      });
    }

    // Send initial bot message after a short delay
    setTimeout(function () {
      addBotMessage(
        "Buongiorno! Sono Alessia, l'assistente virtuale dell'Avv. Pagliano. Come posso aiutarla?"
      );
      showOptions([
        "Richiedere una consulenza",
        "Informazioni sui servizi",
        "Contattare lo studio",
      ]);
    }, 800);
  }

  /* ── Toggle ────────────────────────────────────────────── */
  function toggleChat() {
    state.open = !state.open;
    getEls();
    if (!panel) return;
    panel.style.display = state.open ? "block" : "none";
    if (state.open) {
      btn.style.display = "none";
    } else {
      btn.style.display = "flex";
    }
  }

  /* ── Messaging helpers ─────────────────────────────────── */
  function addBotMessage(text, extraClass) {
    getEls();
    var div = document.createElement("div");
    div.className = "chat-msg bot" + (extraClass ? " " + extraClass : "");
    div.innerHTML = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function addUserMessage(text) {
    getEls();
    var div = document.createElement("div");
    div.className = "chat-msg user";
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function showOptions(options) {
    getEls();
    var wrapper = document.createElement("div");
    wrapper.className = "chat-options";
    options.forEach(function (opt) {
      var btnEl = document.createElement("button");
      btnEl.className = "chat-option-btn";
      btnEl.textContent = opt;
      btnEl.addEventListener("click", function () {
        wrapper.remove();
        handleOption(opt);
      });
      wrapper.appendChild(btnEl);
    });
    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
  }

  /* ── Option handlers ───────────────────────────────────── */
  function handleOption(choice) {
    addUserMessage(choice);

    switch (choice) {
      case "Richiedere una consulenza":
        handleConsultFlow();
        break;
      case "Informazioni sui servizi":
        showServices();
        break;
      case "Contattare lo studio":
        showContactInfo();
        break;
    }
  }

  /* ── Consultation flow (multi-step) ────────────────────── */
  function handleConsultFlow() {
    state.step = "ask_name";
    state.flow = {};
    setTimeout(function () {
      addBotMessage(
        "Certamente! Per iniziare le prego di fornirmi questi dati:<br><br><b>1. Nome e Cognome</b>"
      );
    }, 300);
    setTimeout(function () {
      input.placeholder = "Es: Mario Rossi";
      input.value = "";
      input.focus();
      sendBtn.textContent = "Invia";
    }, 900);
  }

  function handleConsultName(val) {
    state.flow.name = val;
    state.step = "ask_email";
    addBotMessage("Grazie! E la sua email?");
    setTimeout(function () {
      input.placeholder = "Es: mario@example.com";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleConsultEmail(val) {
    state.flow.email = val;
    state.step = "ask_phone";
    addBotMessage("Perfetto. E il suo numero di telefono?");
    setTimeout(function () {
      input.placeholder = "Es: +39 333 1234567";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleConsultPhone(val) {
    state.flow.phone = val;
    state.step = "ask_desc";
    addBotMessage(
      "Ultimo passaggio: mi aiuti a descrivere brevemente la sua situazione in 2-3 righe."
    );
    setTimeout(function () {
      input.placeholder = "Es: Ho bisogno di aiuto per una separazione...";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleConsultDesc(val) {
    state.flow.description = val;
    addBotMessage(
      "Grazie! Una richiesta è stata inviata.<br><br>L'Avv. Pagliano o un membro del suo staff La contatterà entro 24 ore."
    );
    state.step = "done";
    // Disable input
    setTimeout(function () {
      if (input) input.disabled = true;
      setTimeout(function () {
        showOptions([
          "Richiedere una consulenza",
          "Informazioni sui servizi",
          "Contattare lo studio",
        ]);
      }, 1500);
    }, 500);
  }

  /* ── Services info ─────────────────────────────────────── */
  function showServices() {
    var html =
      "L'Avv. Pagliano offre i seguenti servizi:<br><br>" +
      "<b>1. Diritto di Famiglia</b><br>" +
      "Separazioni, divorzi, affidamento minori, mantenimento.<br><br>" +
      "<b>2. Recupero Crediti</b><br>" +
      "Pignoramenti, ingiunzioni di pagamento, cause bancarie.<br><br>" +
      "<b>3. Esecuzioni Immobiliari</b><br>" +
      "Libera adesione alle aste immobiliari, opposizioni.<br><br>" +
      "<b>4. Responsabilità Civile</b><br>" +
      "Risarcimenti danni, incidenti stradali, responsabilità medica.";
    addBotMessage(html);
    setTimeout(function () {
      showOptions([
        "Richiedere una consulenza",
        "Informazioni sui servizi",
        "Contattare lo studio",
      ]);
    }, 500);
  }

  /* ── Contact info ──────────────────────────────────────── */
  function showContactInfo() {
    var html =
      "Ecco i contatti dello Studio Legale Pagliano:<br><br>" +
      "📍 <b>Indirizzo:</b><br>Via Gropallo 10/2, 16122 Genova<br><br>" +
      "📞 <b>Telefono:</b><br>" +
      '<a href="tel:+393805279810" style="color:#1FAE72;text-decoration:none;">+39 380 527 9810</a><br><br>' +
      "✉️ <b>Email:</b><br>" +
      '<a href="mailto:studio@avvocatopagliano.it" style="color:#1FAE72;text-decoration:none;">studio@avvocatopagliano.it</a>';
    addBotMessage(html);
    setTimeout(function () {
      showOptions([
        "Richiedere una consulenza",
        "Informazioni sui servizi",
        "Contattare lo studio",
      ]);
    }, 500);
  }

  /* ── Send handler ──────────────────────────────────────── */
  function handleSend() {
    getEls();
    var val = (input.value || "").trim();
    if (!val) return;

    addUserMessage(val);
    input.value = "";

    switch (state.step) {
      case "ask_name":
        handleConsultName(val);
        break;
      case "ask_email":
        handleConsultEmail(val);
        break;
      case "ask_phone":
        handleConsultPhone(val);
        break;
      case "ask_desc":
        handleConsultDesc(val);
        break;
      default:
        // Unknown step — just show a fallback
        addBotMessage(
          "Grazie per il suo messaggio! Un nostro operatore Le risponderà al più presto."
        );
        state.step = "done";
        setTimeout(function () {
          showOptions([
            "Richiedere una consulenza",
            "Informazioni sui servizi",
            "Contattare lo studio",
          ]);
        }, 1500);
    }
  }

  /* ── Start on DOM ready ────────────────────────────────── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
