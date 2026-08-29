/**
 * Pagliano Law Firm — Chat Widget ("Alessia")
 * Standalone: no external dependencies, no API calls.
 * Loaded via <script src="static/chat-widget.js"></script>
 */
(function () {
  "use strict";

  /* ── State ─────────────────────────────────────────────── */
  var state = {
    open: false,
    step: "greeting",
    flow: {}, // accumulates user answers per conversation
    submitting: false,
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
        "Buongiorno! Sono Alessia, l'assistente digitale dello studio legale. Come posso aiutarla?"
      );
      showOptions([
        "Richiedere una consulenza",
        "Prenotare un appuntamento",
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
    var row = document.createElement("div");
    row.className = "chat-row bot";
    var avatar = document.createElement("img");
    avatar.className = "chat-avatar-mini";
    avatar.src = "static/chat-avatar.png";
    avatar.alt = "Alessia";
    var div = document.createElement("div");
    div.className = "chat-msg bot" + (extraClass ? " " + extraClass : "");
    div.innerHTML = text;
    row.appendChild(avatar);
    row.appendChild(div);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
  }

  function addUserMessage(text) {
    getEls();
    var row = document.createElement("div");
    row.className = "chat-row user";
    var div = document.createElement("div");
    div.className = "chat-msg user";
    div.textContent = text;
    row.appendChild(div);
    messages.appendChild(row);
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
      case "Prenotare un appuntamento":
        handleAppointmentFlow();
        break;
      case "Informazioni sui servizi":
        showServices();
        break;
      case "Contattare lo studio":
        showContactInfo();
        break;
      case "Nello studio (Via Gropallo 10/2, Genova)":
        handleApptMode(choice);
        break;
      case "Per telefono":
        handleApptMode(choice);
        break;
    }
  }

  /* ── Appointment booking flow ──────────────────────────── */
  function handleAppointmentFlow() {
    state.step = "appt_name";
    state.flow = {};
    setTimeout(function () {
      addBotMessage(
        "Certamente! Posso prenotare un appuntamento per Lei. <br><br><b>1. Nome e Cognome</b>"
      );
    }, 300);
    setTimeout(function () {
      input.placeholder = "Es: Mario Rossi";
      input.value = "";
      input.focus();
      sendBtn.textContent = "Invia";
    }, 900);
  }

  function handleApptName(val) {
    state.flow.name = val;
    state.step = "appt_email";
    addBotMessage("Grazie! E la sua email?");
    setTimeout(function () {
      input.placeholder = "Es: mario@example.com";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleApptEmail(val) {
    state.flow.email = val;
    state.step = "appt_phone";
    addBotMessage("Perfetto. E il suo numero di telefono?");
    setTimeout(function () {
      input.placeholder = "Es: +39 333 1234567";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleApptPhone(val) {
    state.flow.phone = val;
    state.step = "appt_mode";
    addBotMessage("Dove preferisce l'appuntamento?");
    setTimeout(function () {
      input.placeholder = "";
      input.value = "";
      showOptions(["Nello studio (Via Gropallo 10/2, Genova)", "Per telefono"]);
    }, 300);
  }

  function handleApptMode(choice) {
    state.flow.mode = choice;
    state.step = "appt_date";
    addBotMessage(
      "Quale data preferisce? <br><br><i>Formato: giorno/mese/anno, es. 15/09/2026</i>"
    );
    setTimeout(function () {
      input.placeholder = "Es: 15/09/2026";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleApptDate(val) {
    var m = val.trim().match(/^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})$/);
    var iso = val.trim().match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (!m && !iso) {
      addBotMessage(
        "Non ho capito la data. Può riscriverla nel formato giorno/mese/anno, es. 15/09/2026?"
      );
      return;
    }
    var day, month, year;
    if (m) {
      day = parseInt(m[1], 10);
      month = parseInt(m[2], 10);
      year = parseInt(m[3], 10);
      if (year < 100) year += 2000;
    } else {
      year = parseInt(iso[1], 10);
      month = parseInt(iso[2], 10);
      day = parseInt(iso[3], 10);
    }
    if (month < 1 || month > 12 || day < 1 || day > 31) {
      addBotMessage(
        "Non ho capito la data. Può riscriverla nel formato giorno/mese/anno, es. 15/09/2026?"
      );
      return;
    }
    state.flow.dateISO =
      year + "-" + (month < 10 ? "0" + month : "" + month) + "-" + (day < 10 ? "0" + day : "" + day);
    state.step = "appt_time";
    addBotMessage(
      "A che ora preferisce? <br><br><i>Formato: ore:minuti, es. 10:00</i>"
    );
    setTimeout(function () {
      input.placeholder = "Es: 10:00";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleApptTime(val) {
    var m = val.trim().match(/^(\d{1,2})[.:]?(\d{0,2})$/);
    if (!m) {
      addBotMessage(
        "Non ho capito l'orario. Può riscriverlo nel formato ore:minuti, es. 10:00?"
      );
      return;
    }
    var hour = parseInt(m[1], 10);
    var minutes = m[2] ? parseInt(m[2], 10) : 0;
    if (hour > 23 || minutes > 59) {
      addBotMessage(
        "Non ho capito l'orario. Può riscriverlo nel formato ore:minuti, es. 10:00?"
      );
      return;
    }
    state.flow.eventISO =
      state.flow.dateISO +
      "T" +
      (hour < 10 ? "0" + hour : "" + hour) +
      ":" +
      (minutes < 10 ? "0" + minutes : "" + minutes) +
      ":00";
    state.step = "appt_desc";
    addBotMessage(
      "Ultimo passaggio: mi aiuti a descrivere brevemente il motivo dell'appuntamento in 2-3 righe. <br><br><i>Questo ci aiuterà a prepararsi al meglio.</i>"
    );
    setTimeout(function () {
      input.placeholder = "Es: Ho bisogno di una consulenza per una separazione...";
      input.value = "";
      input.focus();
    }, 300);
  }

  function handleApptDesc(val) {
    state.flow.description = val;
    addBotMessage("⏳ Sto inviando la richiesta allo studio...");

    var isPhone = state.flow.mode === "Per telefono";
    var payload = {
      fullname: state.flow.name,
      email: state.flow.email,
      phone: state.flow.phone,
      event_date: state.flow.eventISO,
      title: "Appuntamento — " + (isPhone ? "per telefono" : "in studio"),
      description: state.flow.description,
      location: isPhone
        ? "Telefono"
        : "Studio Legale — Via Gropallo 10/2, 16122 Genova",
      gdpr_consent: true,
      source: "pagliano_chatbot",
    };

    fetch("https://web-production-031a6.up.railway.app/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        return resp.json();
      })
      .then(function (result) {
        if (result.error) {
          addBotMessage(
            "Mi spiace, si è verificato un errore nell'invio. Per cortesia, provi a usare il modulo di contatto nella pagina principale, oppure ci chiami al <a href=\"tel:+393805279810\" style=\"color:#698269;\">+39 380 527 9810</a>."
          );
        } else {
          var datePart = state.flow.eventISO.split("T");
          addBotMessage(
            "Appuntamento richiesto con successo! ✓<br><br>" +
              "L'Avv. Pagliano o un membro del suo staff La contatterà entro 24 ore per confermare data e ora.<br><br>" +
              "<b>Riepilogo:</b><br>" +
              "📧 " + state.flow.email + "<br>" +
              "📞 " + state.flow.phone + "<br>" +
              "📅 " + datePart[0] + " alle ore " + datePart[1].slice(0, 5) + "<br>" +
              "📍 " + state.flow.mode
          );
        }
      })
      .catch(function (err) {
        addBotMessage(
          "Mi spiace, si è verificato un errore nell'invio. Per cortesia, provi a usare il modulo di contatto nella pagina principale, oppure ci chiami al <a href=\"tel:+393805279810\" style=\"color:#698269;\">+39 380 527 9810</a>."
        );
      })
      .finally(function () {
        setTimeout(function () {
          showOptions([
            "Richiedere una consulenza",
            "Prenotare un appuntamento",
            "Informazioni sui servizi",
            "Contattare lo studio",
          ]);
        }, 1500);
      });

    state.step = "done";
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
    state.flow.source = "pagliano_chatbot";
    state.flow.gdpr_consent = true;
    state.flow.practice_area = "Altro";

    // Post to CRM intake endpoint
    submitToCRM(state.flow, "consultation");
    state.step = "done";
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
      '<a href="tel:+393805279810" style="color:#698269;text-decoration:none;">+39 380 527 9810</a><br><br>' +
      "✉️ <b>Email:</b><br>" +
      '<a href="mailto:studio@avvocatopagliano.it" style="color:#698269;text-decoration:none;">studio@avvocatopagliano.it</a>';
    addBotMessage(html);
    setTimeout(function () {
      showOptions([
        "Richiedere una consulenza",
        "Informazioni sui servizi",
        "Contattare lo studio",
      ]);
    }, 500);
  }

  /* ── CRM submission helper ─────────────────────────────── */
  function submitToCRM(data, type) {
    addBotMessage("⏳ Sto inviando la richiesta allo studio...");

    var payload = new FormData();
    payload.append("fullname", data.name || "");
    payload.append("email", data.email || "");
    payload.append("phone", data.phone || "");
    payload.append("message", data.description || "");
    payload.append("practice_area", data.practice_area || "Altro");
    payload.append("source", data.source || "pagliano_chatbot");
    payload.append("gdpr_consent", "true");
    if (data.date) {
      payload.append("appointment_date", data.date);
    }
    if (type === "appointment") {
      payload.append("intent", "appointment");
    }

    fetch("https://web-production-031a6.up.railway.app/api/intake/pagliano", {
      method: "POST",
      body: payload,
    })
      .then(function (resp) {
        return resp.json();
      })
      .then(function (result) {
        if (result.error) {
          addBotMessage(
            "Mi spiace, si è verificato un errore. " +
              "Per cortesia, provi a usare il modulo di contatto " +
              'nella pagina principale, oppure ci chiami al <a href="tel:+393805279810" style="color:#698269;">+39 380 527 9810</a>.'
          );
        } else {
          var msg = "";
          if (type === "appointment") {
            msg =
              "Appuntamento prenotato con successo! ✓<br><br>" +
              "L'Avv. Pagliano o un membro del suo staff La contatterà " +
              "entro 24 ore per confermare la data e l'ora.<br><br>" +
              '<b>Riepilogo:</b><br>' +
              "📧 " + data.email + "<br>" +
              "📞 " + data.phone + "<br>" +
              "📅 " + data.date;
          } else {
            msg =
              "Richiesta inviata con successo! ✓<br><br>" +
              "L'Avv. Pagliano o un membro del suo staff La contatterà " +
              "entro 24 ore per fissare un appuntamento.";
          }
          addBotMessage(msg);
        }
      })
      .catch(function (err) {
        addBotMessage(
          "Errore di connessione. " +
            'Per cortesia, provi a usare il modulo di contatto ' +
            'nella pagina principale, oppure ci chiami al <a href="tel:+393805279810" style="color:#698269;">+39 380 527 9810</a>.'
        );
      })
      .finally(function () {
        setTimeout(function () {
          showOptions([
            "Richiedere una consulenza",
            "Prenotare un appuntamento",
            "Informazioni sui servizi",
            "Contattare lo studio",
          ]);
        }, 1500);
      });
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
      case "appt_name":
        handleApptName(val);
        break;
      case "appt_email":
        handleApptEmail(val);
        break;
      case "appt_phone":
        handleApptPhone(val);
        break;
      case "appt_date":
        handleApptDate(val);
        break;
      case "appt_time":
        handleApptTime(val);
        break;
      case "appt_desc":
        handleApptDesc(val);
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
