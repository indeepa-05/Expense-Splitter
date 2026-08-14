"use strict";

const state = {
  people: [],
  expenses: [],
  editingExpenseId: null,
};

const elements = {
  message: document.querySelector("#message"),
  newSession: document.querySelector("#new-session"),
  personForm: document.querySelector("#person-form"),
  personName: document.querySelector("#person-name"),
  peopleList: document.querySelector("#people-list"),
  peopleCount: document.querySelector("#people-count"),
  expenseForm: document.querySelector("#expense-form"),
  expenseHeading: document.querySelector("#expense-form-heading"),
  expenseDescription: document.querySelector("#expense-description"),
  expenseAmount: document.querySelector("#expense-amount"),
  expensePayer: document.querySelector("#expense-payer"),
  expenseSubmit: document.querySelector("#expense-submit"),
  cancelEdit: document.querySelector("#cancel-edit"),
  editBadge: document.querySelector("#edit-badge"),
  equalParticipants: document.querySelector("#equal-participants"),
  percentageParticipants: document.querySelector("#percentage-participants"),
  equalSelectAll: document.querySelector("#equal-select-all"),
  percentageSelectAll: document.querySelector("#percentage-select-all"),
  equalSelectAllControl: document.querySelector("#equal-select-all-control"),
  percentageSelectAllControl: document.querySelector("#percentage-select-all-control"),
  percentageSummary: document.querySelector("#percentage-summary"),
  percentageTotal: document.querySelector("#percentage-total"),
  percentageRemaining: document.querySelector("#percentage-remaining"),
  expensesList: document.querySelector("#expenses-list"),
  balancesList: document.querySelector("#balances-list"),
  settlementsList: document.querySelector("#settlements-list"),
};

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item.msg).join("; ");
    }
    throw new Error(detail || "Something went wrong. Please try again.");
  }
  return data;
}

function showMessage(message, type = "success") {
  elements.message.textContent = message;
  elements.message.className = `message ${type}`;
  elements.message.hidden = false;
  elements.message.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearMessage() {
  elements.message.hidden = true;
  elements.message.textContent = "";
}

function createElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function emptyState(text) {
  return createElement("p", "empty-state", text);
}

function personName(personId) {
  return state.people.find((person) => person.id === Number(personId))?.name || `Person ${personId}`;
}

function formatCents(amountCents) {
  const raw = String(amountCents);
  const negative = raw.startsWith("-");
  const digits = (negative ? raw.slice(1) : raw).padStart(3, "0");
  const rupees = digits.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const cents = digits.slice(-2);
  return `${negative ? "-" : ""}Rs. ${rupees}.${cents}`;
}

function centsToAmountInput(amountCents) {
  const digits = String(amountCents).padStart(3, "0");
  return `${digits.slice(0, -2)}.${digits.slice(-2)}`;
}

function selectedSplitType() {
  return document.querySelector('input[name="split-type"]:checked').value;
}

function renderPeople() {
  elements.peopleList.replaceChildren();
  elements.peopleCount.textContent = `${state.people.length} ${state.people.length === 1 ? "person" : "people"}`;
  if (!state.people.length) {
    elements.peopleList.append(emptyState("No people added yet."));
  } else {
    state.people.forEach((person) => {
      const chip = createElement("span", "person-chip");
      const remove = createElement("button", "person-remove", "Remove");
      remove.type = "button";
      remove.setAttribute("aria-label", `Remove ${person.name}`);
      remove.addEventListener("click", () => removePerson(person));
      chip.append(createElement("span", "", person.name), remove);
      elements.peopleList.append(chip);
    });
  }

  elements.expensePayer.replaceChildren();
  if (!state.people.length) {
    const option = createElement("option", "", "Add a person first");
    option.value = "";
    elements.expensePayer.append(option);
  } else {
    state.people.forEach((person) => {
      const option = createElement("option", "", person.name);
      option.value = String(person.id);
      elements.expensePayer.append(option);
    });
  }
  elements.expensePayer.disabled = !state.people.length;
  elements.expenseSubmit.disabled = !state.people.length;
  renderParticipantControls();
  if (state.editingExpenseId !== null) {
    const expense = state.expenses.find((item) => item.id === state.editingExpenseId);
    if (expense) applyExpenseParticipantState(expense);
  }
}

function participantRow(person, mode) {
  const row = createElement("label", "participant-row");
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.value = String(person.id);
  checkbox.dataset.participantId = String(person.id);
  checkbox.dataset.mode = mode;
  const name = createElement("span", "participant-name", person.name);
  row.append(checkbox, name);

  checkbox.addEventListener("change", () => {
    if (mode === "percentage") {
      const input = row.querySelector(".percentage-input");
      input.disabled = !checkbox.checked;
      input.required = checkbox.checked;
      if (!checkbox.checked) input.value = "";
      updatePercentageSummary();
    }
    syncSelectAllState(mode);
  });

  if (mode === "percentage") {
    const input = document.createElement("input");
    input.type = "number";
    input.inputMode = "decimal";
    input.min = "0.01";
    input.max = "100";
    input.step = "0.01";
    input.placeholder = "0.00";
    input.className = "percentage-input";
    input.dataset.percentageId = String(person.id);
    input.disabled = true;
    input.setAttribute("aria-label", `${person.name} percentage`);
    input.addEventListener("input", updatePercentageSummary);
    row.append(input, createElement("span", "", "%"));
  }
  return row;
}

function renderParticipantControls() {
  elements.equalParticipants.replaceChildren();
  elements.percentageParticipants.replaceChildren();
  if (!state.people.length) {
    const message = emptyState("Add people before creating an expense.");
    elements.equalParticipants.append(message);
    elements.percentageParticipants.append(message.cloneNode(true));
    syncSelectAllState("equal");
    syncSelectAllState("percentage");
    updatePercentageSummary();
    return;
  }
  state.people.forEach((person) => {
    elements.equalParticipants.append(participantRow(person, "equal"));
    elements.percentageParticipants.append(participantRow(person, "percentage"));
  });
  syncSelectAllState("equal");
  syncSelectAllState("percentage");
  updateSplitMode();
}

function participantContainer(mode) {
  return mode === "equal" ? elements.equalParticipants : elements.percentageParticipants;
}

function selectAllCheckbox(mode) {
  return mode === "equal" ? elements.equalSelectAll : elements.percentageSelectAll;
}

function syncSelectAllState(mode) {
  const checkboxes = Array.from(
    participantContainer(mode).querySelectorAll('input[type="checkbox"]'),
  );
  const selectAll = selectAllCheckbox(mode);
  selectAll.checked = checkboxes.length > 0 && checkboxes.every((checkbox) => checkbox.checked);
  selectAll.disabled = checkboxes.length === 0;
}

function setAllParticipants(mode, checked) {
  participantContainer(mode).querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.checked = checked;
    if (mode === "percentage") {
      const input = checkbox.closest(".participant-row").querySelector(".percentage-input");
      input.disabled = !checked;
      input.required = checked;
      if (!checked) input.value = "";
    }
  });
  syncSelectAllState(mode);
  if (mode === "percentage") updatePercentageSummary();
}

function percentageToHundredths(value) {
  const match = value.trim().match(/^(\d+)(?:\.(\d{0,2}))?$/);
  if (!match) return 0;
  return Number(match[1]) * 100 + Number((match[2] || "").padEnd(2, "0"));
}

function updatePercentageSummary() {
  let total = 0;
  elements.percentageParticipants.querySelectorAll('input[type="checkbox"]:checked').forEach((checkbox) => {
    const input = elements.percentageParticipants.querySelector(`[data-percentage-id="${checkbox.value}"]`);
    total += percentageToHundredths(input.value);
  });
  elements.percentageTotal.textContent = `Total: ${Math.floor(total / 100)}.${String(total % 100).padStart(2, "0")}%`;
  const difference = Math.abs(10000 - total);
  const formattedDifference = `${Math.floor(difference / 100)}.${String(difference % 100).padStart(2, "0")}%`;
  if (total > 10000) {
    elements.percentageRemaining.textContent = `Over by: ${formattedDifference}`;
    elements.percentageSummary.classList.add("over-limit");
  } else {
    elements.percentageRemaining.textContent = `Remaining: ${formattedDifference}`;
    elements.percentageSummary.classList.remove("over-limit");
  }
}

function updateSplitMode() {
  const percentageMode = selectedSplitType() === "percentage";
  elements.equalParticipants.hidden = percentageMode;
  elements.percentageParticipants.hidden = !percentageMode;
  elements.equalSelectAllControl.hidden = percentageMode;
  elements.percentageSelectAllControl.hidden = !percentageMode;
  elements.percentageSummary.hidden = !percentageMode;
  syncSelectAllState(percentageMode ? "percentage" : "equal");
  if (percentageMode) updatePercentageSummary();
}

function normalizeMoneyInput() {
  const cleaned = elements.expenseAmount.value.trim();
  const match = cleaned.match(/^(\d+)(?:\.(\d{1,2}))?$/);
  if (!match) return;

  const whole = match[1];
  const fraction = match[2] || "";
  if (!/[1-9]/.test(`${whole}${fraction}`)) return;
  elements.expenseAmount.value = `${whole}.${fraction.padEnd(2, "0")}`;
}

function expenseRequestFromForm() {
  const splitType = selectedSplitType();
  const request = {
    description: elements.expenseDescription.value,
    amount: elements.expenseAmount.value.trim(),
    payer_id: Number(elements.expensePayer.value),
    split_type: splitType,
  };

  if (splitType === "equal") {
    request.participant_ids = Array.from(
      elements.equalParticipants.querySelectorAll('input[type="checkbox"]:checked'),
      (checkbox) => Number(checkbox.value),
    );
    if (!request.participant_ids.length) throw new Error("Select at least one participant.");
  } else {
    request.percentages = {};
    elements.percentageParticipants.querySelectorAll('input[type="checkbox"]:checked').forEach((checkbox) => {
      const input = elements.percentageParticipants.querySelector(`[data-percentage-id="${checkbox.value}"]`);
      request.percentages[checkbox.value] = input.value.trim();
    });
    if (!Object.keys(request.percentages).length) throw new Error("Select at least one participant.");
  }
  return request;
}

function renderExpenses() {
  elements.expensesList.replaceChildren();
  if (!state.expenses.length) {
    elements.expensesList.append(emptyState("No expenses recorded yet."));
    return;
  }

  state.expenses.forEach((expense) => {
    const card = createElement("article", "expense-card");
    const header = createElement("div", "expense-card-header");
    header.append(
      createElement("h3", "", expense.description || "Untitled expense"),
      createElement("span", "expense-amount", formatCents(expense.amount_cents)),
    );
    const splitLabel = expense.split_type === "equal" ? "Equal" : "Percentage";
    const meta = createElement("p", "expense-meta", `Paid by ${personName(expense.payer_id)} · ${splitLabel} split`);
    const shares = createElement("ul", "share-list");
    expense.participant_ids.forEach((participantId) => {
      const row = createElement("li", "share-row");
      const percentage = expense.percentages?.[String(participantId)];
      const label = percentage === undefined
        ? personName(participantId)
        : `${personName(participantId)} · ${percentage}%`;
      row.append(
        createElement("span", "", label),
        createElement("strong", "", formatCents(expense.shares[String(participantId)])),
      );
      shares.append(row);
    });
    const actions = createElement("div", "expense-actions");
    const edit = createElement("button", "button-secondary button-small", "Edit");
    edit.type = "button";
    edit.addEventListener("click", () => beginEdit(expense));
    const remove = createElement("button", "button-danger button-small", "Delete");
    remove.type = "button";
    remove.addEventListener("click", () => deleteExpense(expense));
    actions.append(edit, remove);
    card.append(header, meta, shares, actions);
    elements.expensesList.append(card);
  });
}

function renderBalances(balances) {
  elements.balancesList.replaceChildren();
  if (!balances.length) {
    elements.balancesList.append(emptyState("Add people to start tracking balances."));
    return;
  }
  const labels = { receive: "To receive", owes: "Owes", settled: "Settled" };
  balances.forEach((balance) => {
    const row = createElement("div", `balance-row ${balance.status}`);
    const detail = createElement("div", "balance-detail");
    detail.append(
      createElement("span", "balance-value", balance.balance),
      createElement("span", "balance-status", labels[balance.status]),
    );
    row.append(createElement("span", "balance-name", balance.name), detail);
    elements.balancesList.append(row);
  });
}

function renderSettlements(settlements) {
  elements.settlementsList.replaceChildren();
  if (!settlements.length) {
    elements.settlementsList.append(emptyState("Everyone is settled."));
    return;
  }
  settlements.forEach((settlement) => {
    const row = createElement("div", "settlement-row");
    row.append(
      createElement("span", "settlement-copy", `${settlement.from_name} pays ${settlement.to_name}`),
      createElement("strong", "", settlement.amount),
    );
    elements.settlementsList.append(row);
  });
}

async function loadPeople() {
  state.people = await apiRequest("/api/people");
  renderPeople();
}

async function loadExpenses() {
  state.expenses = await apiRequest("/api/expenses");
  renderExpenses();
}

async function loadBalances() {
  renderBalances(await apiRequest("/api/balances"));
}

async function loadSettlements() {
  renderSettlements(await apiRequest("/api/settlements"));
}

async function refreshAll() {
  await loadPeople();
  await Promise.all([loadExpenses(), loadBalances(), loadSettlements()]);
}

function resetExpenseForm() {
  state.editingExpenseId = null;
  elements.expenseForm.reset();
  elements.expenseHeading.textContent = "Add Expense";
  elements.expenseSubmit.textContent = "Add Expense";
  elements.cancelEdit.hidden = true;
  elements.editBadge.hidden = true;
  renderParticipantControls();
  updateSplitMode();
}

function beginEdit(expense) {
  clearMessage();
  state.editingExpenseId = expense.id;
  elements.expenseHeading.textContent = "Edit Expense";
  elements.expenseSubmit.textContent = "Save Changes";
  elements.cancelEdit.hidden = false;
  elements.editBadge.hidden = false;
  elements.expenseDescription.value = expense.description;
  elements.expenseAmount.value = centsToAmountInput(expense.amount_cents);
  document.querySelector(`input[name="split-type"][value="${expense.split_type}"]`).checked = true;
  renderParticipantControls();
  updateSplitMode();

  applyExpenseParticipantState(expense);
  document.querySelector("#expense-form-section").scrollIntoView({ behavior: "smooth" });
}

function applyExpenseParticipantState(expense) {
  elements.expensePayer.value = String(expense.payer_id);

  if (expense.split_type === "equal") {
    expense.participant_ids.forEach((personId) => {
      const checkbox = elements.equalParticipants.querySelector(`[data-participant-id="${personId}"]`);
      if (checkbox) checkbox.checked = true;
    });
    syncSelectAllState("equal");
  } else {
    expense.participant_ids.forEach((personId) => {
      const checkbox = elements.percentageParticipants.querySelector(`[data-participant-id="${personId}"]`);
      const input = elements.percentageParticipants.querySelector(`[data-percentage-id="${personId}"]`);
      if (checkbox && input) {
        checkbox.checked = true;
        input.disabled = false;
        input.required = true;
        input.value = expense.percentages[String(personId)];
      }
    });
    syncSelectAllState("percentage");
    updatePercentageSummary();
  }
}

async function deleteExpense(expense) {
  if (!window.confirm(`Delete ${expense.description || "this expense"}?`)) return;
  try {
    await apiRequest(`/api/expenses/${expense.id}`, { method: "DELETE" });
    if (state.editingExpenseId === expense.id) resetExpenseForm();
    await Promise.all([loadExpenses(), loadBalances(), loadSettlements()]);
    showMessage("Expense deleted.");
  } catch (error) {
    showMessage(error.message, "error");
  }
}

async function removePerson(person) {
  if (!window.confirm(`Remove ${person.name}?`)) return;
  clearMessage();
  try {
    await apiRequest(`/api/people/${person.id}`, { method: "DELETE" });
    await loadPeople();
    await Promise.all([loadBalances(), loadSettlements()]);
    showMessage(`${person.name} removed.`);
  } catch (error) {
    showMessage(error.message, "error");
  }
}

async function startNewSession() {
  const confirmed = window.confirm(
    "Start a new session?\n\nThis will permanently clear all people and expenses from the current session.",
  );
  if (!confirmed) return;

  clearMessage();
  try {
    await apiRequest("/api/session", { method: "DELETE" });
    elements.personName.value = "";
    resetExpenseForm();
    await refreshAll();
    showMessage("New session started.");
  } catch (error) {
    showMessage(error.message, "error");
  }
}

elements.personForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();
  try {
    await apiRequest("/api/people", {
      method: "POST",
      body: JSON.stringify({ name: elements.personName.value }),
    });
    elements.personName.value = "";
    await refreshAll();
    showMessage("Person added.");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

elements.expenseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearMessage();
  try {
    const request = expenseRequestFromForm();
    const editing = state.editingExpenseId !== null;
    await apiRequest(editing ? `/api/expenses/${state.editingExpenseId}` : "/api/expenses", {
      method: editing ? "PUT" : "POST",
      body: JSON.stringify(request),
    });
    resetExpenseForm();
    await Promise.all([loadExpenses(), loadBalances(), loadSettlements()]);
    showMessage(editing ? "Expense updated." : "Expense added.");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

document.querySelectorAll('input[name="split-type"]').forEach((input) => {
  input.addEventListener("change", updateSplitMode);
});
elements.equalSelectAll.addEventListener("change", () => {
  setAllParticipants("equal", elements.equalSelectAll.checked);
});
elements.percentageSelectAll.addEventListener("change", () => {
  setAllParticipants("percentage", elements.percentageSelectAll.checked);
});
elements.expenseAmount.addEventListener("blur", normalizeMoneyInput);
elements.cancelEdit.addEventListener("click", resetExpenseForm);
elements.newSession.addEventListener("click", startNewSession);

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await refreshAll();
  } catch (error) {
    showMessage(error.message, "error");
  }
});
