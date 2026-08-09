(function () {
  "use strict";

  var CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').content;

  function escapeHtml(str) {
    // Defense in depth: even though server-side validation already restricts
    // characters, never trust stored data when injecting into innerHTML.
    var div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  function api(path, options) {
    options = options || {};
    options.headers = Object.assign({}, options.headers, {
      "X-CSRFToken": CSRF_TOKEN,
    });
    if (options.body && !(options.body instanceof FormData)) {
      options.headers["Content-Type"] = "application/json";
    }
    return fetch(path, options).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (body) {
          throw new Error(body.error || "request failed (" + res.status + ")");
        });
      }
      var ct = res.headers.get("content-type") || "";
      return ct.indexOf("application/json") !== -1 ? res.json() : res.text();
    });
  }

  // --- Tabs -----------------------------------------------------------------------
  document.querySelectorAll(".tab").forEach(function (tabBtn) {
    tabBtn.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("active"); });
      document.querySelectorAll(".panel").forEach(function (p) { p.classList.remove("active"); });
      tabBtn.classList.add("active");
      document.getElementById("tab-" + tabBtn.dataset.tab).classList.add("active");
      loadTab(tabBtn.dataset.tab);
    });
  });

  function loadTab(name) {
    if (name === "overview") loadOverview();
    if (name === "registrations") loadRegistrations();
    if (name === "events") loadEvents();
    if (name === "audit") loadAudit();
  }

  // --- Overview ---------------------------------------------------------------------
  function loadOverview() {
    api("/admin/api/summary").then(function (data) {
      document.getElementById("overview-cards").innerHTML =
        '<div class="card"><div class="num">' + data.total_registrations + '</div><div class="label">Total registrations</div></div>' +
        '<div class="card"><div class="num">' + data.total_events + '</div><div class="label">Events</div></div>';

      var tbody = document.querySelector("#overview-table tbody");
      tbody.innerHTML = data.by_event.map(function (row) {
        return "<tr><td>" + escapeHtml(row.event_name) + "</td><td>" + row.count + "</td></tr>";
      }).join("");
    }).catch(showError);
  }

  // --- Registrations ------------------------------------------------------------------
  var currentEvents = [];

  function populateEventFilter() {
    var sel = document.getElementById("reg-event-filter");
    sel.innerHTML = '<option value="">All events</option>' + currentEvents.map(function (e) {
      return '<option value="' + e.id + '">' + escapeHtml(e.name) + "</option>";
    }).join("");
  }

  function loadRegistrations() {
    api("/admin/api/events").then(function (evs) {
      currentEvents = evs;
      populateEventFilter();
      return fetchRegistrations();
    }).catch(showError);
  }

  function fetchRegistrations() {
    var eventId = document.getElementById("reg-event-filter").value;
    var qs = eventId ? "?event_id=" + encodeURIComponent(eventId) : "";
    document.getElementById("export-link").href = "/admin/api/registrations/export.csv" + qs;
    return api("/admin/api/registrations" + qs).then(function (rows) {
      var eventNameById = {};
      currentEvents.forEach(function (e) { eventNameById[e.id] = e.name; });

      var tbody = document.querySelector("#reg-table tbody");
      tbody.innerHTML = rows.map(function (r) {
        var eventName = eventNameById[r.event_id] || r.event_id;
        var when = new Date(r.created_at * 1000).toLocaleString();
        return "<tr>" +
          "<td>" + escapeHtml(r.name) + "</td>" +
          "<td>" + escapeHtml(r.email) + "</td>" +
          "<td>" + escapeHtml(r.phone) + "</td>" +
          "<td>" + escapeHtml(eventName) + "</td>" +
          '<td><span class="status-pill status-' + r.status + '">' + r.status + "</span></td>" +
          "<td>" + when + "</td>" +
          '<td class="row-actions">' +
            '<button data-action="confirm" data-id="' + r.id + '">Confirm</button>' +
            '<button data-action="cancel" data-id="' + r.id + '">Cancel</button>' +
            '<button data-action="delete" data-id="' + r.id + '">Delete</button>' +
          "</td>" +
        "</tr>";
      }).join("");
    });
  }

  document.getElementById("reg-event-filter").addEventListener("change", fetchRegistrations);

  document.querySelector("#reg-table tbody").addEventListener("click", function (e) {
    var btn = e.target.closest("button");
    if (!btn) return;
    var id = btn.dataset.id;
    var action = btn.dataset.action;

    if (action === "delete") {
      if (!confirm("Delete this registration? This cannot be undone.")) return;
      api("/admin/api/registrations/" + id, { method: "DELETE" }).then(fetchRegistrations).catch(showError);
      return;
    }

    var status = action === "confirm" ? "confirmed" : "cancelled";
    api("/admin/api/registrations/" + id + "/status", {
      method: "POST",
      body: JSON.stringify({ status: status }),
    }).then(fetchRegistrations).catch(showError);
  });

  // --- Events -----------------------------------------------------------------------
  function loadEvents() {
    document.getElementById("event-csrf").value = CSRF_TOKEN;
    return api("/admin/api/events").then(function (rows) {
      currentEvents = rows;
      var tbody = document.querySelector("#events-table tbody");
      tbody.innerHTML = rows.map(function (e) {
        return "<tr>" +
          "<td>" + escapeHtml(e.name) + "</td>" +
          "<td>" + escapeHtml(e.fee) + "</td>" +
          "<td>" + escapeHtml(e.team_size) + "</td>" +
          "<td>" + escapeHtml(e.venue) + "</td>" +
          "<td>" + escapeHtml(e.date) + "</td>" +
          "<td>" + (e.active ? "Yes" : "No") + "</td>" +
          '<td class="row-actions">' +
            '<button data-action="toggle" data-id="' + e.id + '" data-active="' + e.active + '">' + (e.active ? "Deactivate" : "Activate") + "</button>" +
            '<button data-action="delete" data-id="' + e.id + '">Delete</button>' +
          "</td>" +
        "</tr>";
      }).join("");
    }).catch(showError);
  }

  document.getElementById("event-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var form = e.target;
    var payload = {
      name: form.name.value.trim(),
      fee: form.fee.value.trim(),
      team_size: form.team_size.value.trim(),
      venue: form.venue.value.trim(),
      date: form.date.value.trim(),
    };
    api("/admin/api/events", { method: "POST", body: JSON.stringify(payload) })
      .then(function () { form.reset(); return loadEvents(); })
      .catch(showError);
  });

  document.querySelector("#events-table tbody").addEventListener("click", function (e) {
    var btn = e.target.closest("button");
    if (!btn) return;
    var id = btn.dataset.id;

    if (btn.dataset.action === "delete") {
      if (!confirm("Delete this event? Existing registrations for it are kept but the event will disappear from lists.")) return;
      api("/admin/api/events/" + id, { method: "DELETE" }).then(loadEvents).catch(showError);
      return;
    }

    if (btn.dataset.action === "toggle") {
      var nowActive = btn.dataset.active === "true";
      api("/admin/api/events/" + id + "/toggle", {
        method: "POST",
        body: JSON.stringify({ active: !nowActive }),
      }).then(loadEvents).catch(showError);
    }
  });

  // --- Audit log --------------------------------------------------------------------
  function loadAudit() {
    api("/admin/api/audit-log").then(function (rows) {
      var tbody = document.querySelector("#audit-table tbody");
      tbody.innerHTML = rows.map(function (r) {
        var when = new Date(r.timestamp * 1000).toLocaleString();
        return "<tr>" +
          "<td>" + when + "</td>" +
          "<td>" + escapeHtml(r.actor) + "</td>" +
          "<td>" + escapeHtml(r.action) + "</td>" +
          "<td>" + escapeHtml(r.detail) + "</td>" +
          "<td>" + escapeHtml(r.ip) + "</td>" +
        "</tr>";
      }).join("");
    }).catch(showError);
  }

  function showError(err) {
    alert(err.message || "Something went wrong.");
  }

  // Initial load
  loadOverview();
})();
