"use strict";

const state = {
  stageIndex: 0,
  fixtures: null,
  pipeline: "",
};

const elements = {
  stageTabs: document.querySelector("#stage-tabs"),
  stageCount: document.querySelector("#stage-count"),
  stageNumber: document.querySelector("#stage-number"),
  stageTitle: document.querySelector("#stage-title"),
  stageSummary: document.querySelector("#stage-summary"),
  stageInput: document.querySelector("#stage-input"),
  stageOutput: document.querySelector("#stage-output"),
  stageYaml: document.querySelector("#stage-yaml"),
  yamlLines: document.querySelector("#yaml-lines"),
  previousStage: document.querySelector("#previous-stage"),
  nextStage: document.querySelector("#next-stage"),
  themeToggle: document.querySelector("#theme-toggle"),
};

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function pipelineExcerpt([start, end]) {
  return state.pipeline
    .split("\n")
    .slice(start - 1, end)
    .join("\n");
}

function renderTabs() {
  elements.stageTabs.replaceChildren();
  state.fixtures.stages.forEach((stage, index) => {
    const button = document.createElement("button");
    button.className = "stage-tab";
    button.type = "button";
    button.role = "tab";
    button.id = `stage-tab-${index}`;
    button.dataset.stageId = stage.id;
    button.setAttribute("aria-controls", "stage-panel");
    button.textContent = `${index + 1}. ${stage.title}`;
    button.setAttribute("aria-selected", String(index === state.stageIndex));
    button.addEventListener("click", () => showStage(index));
    elements.stageTabs.append(button);
  });
}

function renderStage() {
  const stage = state.fixtures.stages[state.stageIndex];
  const [start, end] = stage.pipeline_lines;

  elements.stageCount.textContent = `${state.stageIndex + 1} of ${state.fixtures.stages.length}`;
  document.querySelector("#stage-panel").setAttribute(
    "aria-labelledby",
    `stage-tab-${state.stageIndex}`,
  );
  elements.stageNumber.textContent = `STAGE ${state.stageIndex + 1}`;
  elements.stageTitle.textContent = stage.title;
  elements.stageSummary.textContent = stage.summary;
  elements.stageInput.textContent = pretty(stage.input);
  elements.stageOutput.textContent = pretty(stage.output);
  elements.stageYaml.textContent = pipelineExcerpt(stage.pipeline_lines);
  elements.yamlLines.textContent = `lines ${start}–${end} from ${state.fixtures.pipeline}`;
  elements.previousStage.disabled = state.stageIndex === 0;
  elements.nextStage.disabled = state.stageIndex === state.fixtures.stages.length - 1;

  Array.from(elements.stageTabs.children).forEach((tab, index) => {
    tab.setAttribute("aria-selected", String(index === state.stageIndex));
    tab.tabIndex = index === state.stageIndex ? 0 : -1;

    if (index === state.stageIndex) {
      tab.setAttribute("aria-current", "step");
    } else {
      tab.removeAttribute("aria-current");
    }
  });
}

function showStage(index) {
  if (!state.fixtures) return;

  const nextIndex = Math.max(0, Math.min(index, state.fixtures.stages.length - 1));

  if (nextIndex === state.stageIndex) return;

  const scrollPosition = window.scrollY;
  state.stageIndex = nextIndex;
  renderStage();
  window.scrollTo({ top: scrollPosition, behavior: "auto" });
  requestAnimationFrame(() => {
    window.scrollTo({ top: scrollPosition, behavior: "auto" });
  });
}

function resultFor(button) {
  return button.closest(".local-action").querySelector(".action-result");
}

function setActionResult(button, message, failed = false) {
  const result = resultFor(button);
  result.textContent = message;
  result.dataset.state = failed ? "error" : "success";
}

async function copyFrom(button) {
  const target = document.getElementById(button.dataset.copyTarget);

  try {
    if (!target) throw new Error("Copy target missing");

    await navigator.clipboard.writeText(target.textContent);
    setActionResult(button, "Copied");
  } catch (error) {
    setActionResult(button, "Copy failed", true);
  }
}

async function downloadAsset(button, assetUrl, name, mediaType) {
  let url;

  try {
    const response = await fetch(assetUrl);

    if (!response.ok) throw new Error("Download source unavailable");

    const contents = await response.text();
    const blob = new Blob([contents], { type: mediaType });
    url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    anchor.click();
    setActionResult(button, "Downloaded");
  } catch (error) {
    setActionResult(button, "Download failed", true);
  } finally {
    if (url) URL.revokeObjectURL(url);
  }
}

function applyTheme(theme) {
  const dark = theme === "dark";
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  elements.themeToggle.setAttribute("aria-pressed", String(dark));
  elements.themeToggle.textContent = dark ? "Light mode" : "Dark mode";
}

function bindControls() {
  elements.previousStage.addEventListener("click", () => showStage(state.stageIndex - 1));
  elements.nextStage.addEventListener("click", () => showStage(state.stageIndex + 1));

  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      showStage(state.stageIndex - 1);
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      showStage(state.stageIndex + 1);
    }
  });

  document.querySelectorAll("[data-copy-target]").forEach((button) => {
    button.addEventListener("click", () => copyFrom(button));
  });

  const fixtureButton = document.querySelector("#download-fixture");
  fixtureButton.addEventListener("click", () => {
    downloadAsset(
      fixtureButton,
      "/fixtures/stages.json?download=1",
      "scada-hivemq-stages.json",
      "application/json",
    );
  });

  const pipelineButton = document.querySelector("#download-pipeline");
  pipelineButton.addEventListener("click", () => {
    downloadAsset(
      pipelineButton,
      "/pipelines/scada-hivemq.yaml?download=1",
      "scada-hivemq.yaml",
      "application/yaml",
    );
  });

  elements.themeToggle.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
    localStorage.setItem("scada-hivemq-theme", nextTheme);
  });
}

async function loadExplorer() {
  const [fixtureResponse, pipelineResponse] = await Promise.all([
    fetch("/fixtures/stages.json"),
    fetch("/pipelines/scada-hivemq.yaml"),
  ]);

  if (!fixtureResponse.ok || !pipelineResponse.ok) {
    throw new Error("Explorer assets could not be loaded");
  }

  state.fixtures = await fixtureResponse.json();
  state.pipeline = await pipelineResponse.text();
  renderTabs();
  renderStage();
}

applyTheme(localStorage.getItem("scada-hivemq-theme") || "light");

bindControls();

loadExplorer().catch(() => {
  elements.stageCount.textContent = "Load failed";
  elements.stageTitle.textContent = "Pipeline explorer unavailable";
  elements.stageSummary.textContent = "The fixture or shipped pipeline could not be loaded.";
});
