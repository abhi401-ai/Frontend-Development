/* ==========================================================================
   EduGenie — app.js
   Wires each tool-card's form to its FastAPI endpoint, handles loading /
   error states, and renders the result in the matching output container.
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".tool-form").forEach((form) => {
    form.addEventListener("submit", (event) => handleSubmit(event, form));
  });
});

async function handleSubmit(event, form) {
  event.preventDefault();

  const endpoint = form.dataset.endpoint;
  const method = form.dataset.method;
  const outputKey = form.dataset.output;
  const outputEl = document.querySelector(`[data-output-for="${outputKey}"]`);
  const button = form.querySelector('button[type="submit"]');

  if (!outputEl || !button) return;

  setLoadingState(form, button, outputEl, true);

  try {
    const fields = collectFields(form);
    const response = await sendRequest(endpoint, method, fields);
    const data = await safeParseJson(response);

    if (!response.ok) {
      const message = (data && data.detail) || "Something went wrong. Please try again.";
      throw new Error(message);
    }

    renderOutput(outputKey, outputEl, data);
  } catch (error) {
    renderError(outputEl, error);
  } finally {
    setLoadingState(form, button, outputEl, false);
  }
}

/** Collect non-empty named fields from a form, coercing number inputs. */
function collectFields(form) {
  const fields = {};
  form.querySelectorAll("input[name], textarea[name], select[name]").forEach((el) => {
    if (el.value === "") return;
    fields[el.name] = el.type === "number" ? Number(el.value) : el.value;
  });
  return fields;
}

/** Send a GET (query string) or POST (JSON body) request. */
function sendRequest(endpoint, method, fields) {
  if (method === "GET") {
    const params = new URLSearchParams(fields);
    return fetch(`${endpoint}?${params.toString()}`, { method: "GET" });
  }

  return fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

async function safeParseJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function setLoadingState(form, button, outputEl, isLoading) {
  button.disabled = isLoading;
  form.classList.toggle("is-loading", isLoading);

  if (isLoading) {
    outputEl.classList.remove("is-error", "is-filled");
    outputEl.innerHTML = `<p class="output__loading"><span class="spark" aria-hidden="true"></span> Granting your wish…</p>`;
  }
}

function renderError(outputEl, error) {
  outputEl.classList.remove("is-filled");
  outputEl.classList.add("is-error");
  const message = (error && error.message) || "Could not reach EduGenie. Check your connection and try again.";
  outputEl.innerHTML = `<p class="output__error">⚠ ${escapeHtml(message)}</p>`;
}

function renderOutput(kind, outputEl, data) {
  outputEl.classList.remove("is-error");
  outputEl.classList.add("is-filled");

  switch (kind) {
    case "qa":
      outputEl.innerHTML = `<p>${escapeHtml(data.answer)}</p>`;
      break;

    case "explain":
      outputEl.innerHTML = `<p>${escapeHtml(data.explanation)}</p>`;
      break;

    case "summarize":
      outputEl.innerHTML = `<p>${escapeHtml(data.summary)}</p>`;
      break;

    case "quiz":
      outputEl.innerHTML = renderQuiz(data.quiz);
      break;

    case "learn":
      outputEl.innerHTML = renderMultiline(data.recommendations);
      break;

    default:
      outputEl.innerHTML = `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
  }
}

function renderQuiz(quiz) {
  if (!Array.isArray(quiz) || quiz.length === 0) {
    return `<p class="output__error">⚠ The quiz came back empty or in an unexpected format.</p>`;
  }

  return quiz
    .map((q, index) => {
      const options = Array.isArray(q.options) ? q.options : [];
      const optionsHtml = options
        .map((opt) => {
          const isCorrect = opt === q.answer;
          return `<li class="${isCorrect ? "is-correct" : ""}">${escapeHtml(opt)}${
            isCorrect ? '<span class="tag">correct</span>' : ""
          }</li>`;
        })
        .join("");

      return `
        <div class="quiz-item">
          <p class="quiz-item__q"><span class="quiz-item__num">Q${index + 1}.</span> ${escapeHtml(q.question)}</p>
          <ul class="quiz-item__options">${optionsHtml}</ul>
        </div>
      `;
    })
    .join("");
}

function renderMultiline(text) {
  const safe = escapeHtml(text || "");
  const paragraphs = safe.split(/\n+/).filter(Boolean);
  return `<div class="output__path">${paragraphs.map((line) => `<p>${line}</p>`).join("")}</div>`;
}

function escapeHtml(value) {
  if (value === undefined || value === null) return "";
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}