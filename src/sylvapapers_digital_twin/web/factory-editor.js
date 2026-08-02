"use strict";

const NODE_KINDS = [
  ["source", "Entrée matière"],
  ["operation", "Opération"],
  ["buffer", "Stock tampon"],
  ["quality_control", "Contrôle qualité"],
  ["sink", "Sortie produit"],
];
const NODE_WIDTH = 190;
const NODE_HEIGHT = 112;
const state = {
  factory: null,
  selectedNode: null,
  selectedEdge: null,
  connectSource: null,
  connectMode: false,
  armedKind: null,
  drag: null,
  history: [],
  future: [],
  validatedSnapshot: null,
};

const byId = (id) => document.getElementById(id);
const graphCanvas = byId("graph-canvas");
const nodeLayer = byId("node-layer");
const edgeLayer = byId("edge-layer");

function cleanList(value) {
  if (Array.isArray(value)) return value.map(String).map((item) => item.trim()).filter(Boolean);
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

function status(message, error = false) {
  const element = byId("status");
  element.textContent = message;
  element.classList.toggle("error", error);
}

function serialise() { return JSON.stringify(state.factory); }

function checkpoint() {
  if (state.factory) state.history.push(serialise());
  if (state.history.length > 80) state.history.shift();
  state.future = [];
  state.validatedSnapshot = null;
  byId("write-config").disabled = true;
}

function restore(snapshot) {
  state.factory = normalizeFactory(JSON.parse(snapshot));
  state.selectedNode = null;
  state.selectedEdge = null;
  state.connectSource = null;
  state.validatedSnapshot = null;
  render();
}

function undo() {
  if (!state.history.length) return;
  state.future.push(serialise());
  restore(state.history.pop());
  status("Modification annulée.");
}

function redo() {
  if (!state.future.length) return;
  state.history.push(serialise());
  restore(state.future.pop());
  status("Modification rétablie.");
}

function densityFor(machineType) {
  return state.factory.machine_types.find((item) => item.machine_type === machineType)?.failure_density;
}

function densityText(machineType) {
  const density = densityFor(machineType);
  if (!density) return "Densité de panne manquante";
  return `Weibull · β ${density.shape} · η ${density.scale_hours} h de fonctionnement`;
}

function normalizeFactory(payload) {
  const factory = payload && payload.factory ? payload.factory : payload;
  if (!factory || typeof factory !== "object") throw new Error("Le JSON ne contient pas de configuration usine.");
  factory.schema_version ||= "1.0.0";
  factory.provenance ||= "user-edited-not-calibrated";
  factory.timezone ||= "Europe/Paris";
  factory.machine_types ||= [];
  factory.machines ||= [];
  factory.process_graph ||= {schema_version: "1.0.0", provenance: "user-edited", nodes: [], edges: []};
  factory.process_graph.nodes ||= [];
  factory.process_graph.edges ||= [];
  factory.resource_calendars ||= [];
  factory.process_graph.nodes.forEach((node, index) => {
    node.machine_ids ||= [];
    node.input_materials ||= [];
    node.output_materials ||= [];
    node.position ||= {x: 80 + (index % 6) * 250, y: 80 + Math.floor(index / 6) * 180};
  });
  factory.machine_types.forEach((type) => {
    type.failure_density ||= {family: "weibull", shape: 2, scale_hours: 1500};
    type.failure_density.family = "weibull";
    delete type.failure_density.location_hours;
    type.metadata ||= {calibration_status: "synthetic_hypothesis"};
  });
  return factory;
}

function validateFactory(factory = state.factory) {
  const errors = [];
  if (!factory.factory_id?.trim()) errors.push("factory_id est requis");
  if (!factory.name?.trim()) errors.push("le nom de l'usine est requis");
  if (!Array.isArray(factory.machines) || !factory.machines.length) errors.push("au moins une machine est requise");
  const machineIds = factory.machines.map((machine) => machine.machine_id);
  const machineTypes = new Set(factory.machine_types.map((type) => type.machine_type));
  if (new Set(machineIds).size !== machineIds.length) errors.push("les identifiants machine doivent être uniques");
  factory.machines.forEach((machine) => {
    if (!machineTypes.has(machine.machine_type)) errors.push(`type inconnu pour ${machine.machine_id}`);
    if (!(Number(machine.capacity_per_hour) > 0)) errors.push(`capacité invalide pour ${machine.machine_id}`);
    if (!(Number(machine.availability) > 0 && Number(machine.availability) <= 1)) errors.push(`disponibilité invalide pour ${machine.machine_id}`);
  });
  factory.machine_types.forEach((type) => {
    const density = type.failure_density || {};
    if (density.family !== "weibull") errors.push(`seule la densité Weibull est acceptée (${type.machine_type})`);
    if (!(Number(density.shape) > 0) || !(Number(density.scale_hours) > 0)) {
      errors.push(`coefficients de panne invalides pour ${type.machine_type}`);
    }
  });
  const nodes = factory.process_graph.nodes;
  const nodeIds = nodes.map((node) => node.node_id);
  const knownNodes = new Set(nodeIds);
  if (new Set(nodeIds).size !== nodeIds.length) errors.push("les identifiants d'étape doivent être uniques");
  if (nodes.length < 2) errors.push("le procédé doit comporter au moins deux étapes");
  nodes.forEach((node) => {
    if (node.kind === "operation" && !node.machine_ids.length) errors.push(`${node.node_id} doit référencer une machine`);
    node.machine_ids.forEach((id) => {
      if (!machineIds.includes(id)) errors.push(`${node.node_id} référence la machine inconnue ${id}`);
    });
    if (!Number.isFinite(node.position?.x) || !Number.isFinite(node.position?.y)) errors.push(`position invalide pour ${node.node_id}`);
  });
  const edgeKeys = new Set();
  factory.process_graph.edges.forEach((edge) => {
    if (!knownNodes.has(edge.source) || !knownNodes.has(edge.target)) errors.push(`relation invalide ${edge.source} → ${edge.target}`);
    if (edge.source === edge.target) errors.push(`boucle directe interdite sur ${edge.source}`);
    const key = `${edge.source}\u0000${edge.target}\u0000${edge.condition || ""}`;
    if (edgeKeys.has(key)) errors.push(`relation dupliquée ${edge.source} → ${edge.target}`);
    edgeKeys.add(key);
  });
  return errors;
}

function render() {
  renderPalette();
  renderNodes();
  renderEdges();
  renderInspector();
  byId("factory-summary").textContent = `${state.factory.name} · ${state.factory.machines.length} machines · ${state.factory.process_graph.nodes.length} étapes`;
  byId("edit-selected").disabled = !state.selectedNode;
  byId("duplicate-selected").disabled = !state.selectedNode;
  byId("delete-selected").disabled = !state.selectedNode && !state.selectedEdge;
  byId("undo").disabled = !state.history.length;
  byId("redo").disabled = !state.future.length;
}

function renderPalette() {
  const palette = byId("node-palette");
  palette.replaceChildren();
  NODE_KINDS.forEach(([kind, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.draggable = true;
    button.textContent = `+ ${label}`;
    button.dataset.kind = kind;
    button.setAttribute("aria-pressed", String(state.armedKind === kind));
    button.addEventListener("dragstart", (event) => event.dataTransfer.setData("text/x-node-kind", kind));
    button.addEventListener("click", () => {
      state.armedKind = state.armedKind === kind ? null : kind;
      status(state.armedKind ? "Cliquez sur le plan pour placer l'étape." : "Ajout annulé.");
      renderPalette();
    });
    palette.append(button);
  });
}

function renderNodes() {
  nodeLayer.replaceChildren();
  state.factory.process_graph.nodes.forEach((node) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "process-node";
    if (state.selectedNode === node.node_id) button.classList.add("selected");
    if (state.connectSource === node.node_id) button.classList.add("connect-source");
    button.style.left = `${node.position.x}px`;
    button.style.top = `${node.position.y}px`;
    button.dataset.nodeId = node.node_id;
    button.setAttribute("aria-label", `${node.name}, ${node.kind}. Entrées ${cleanList(node.input_materials).join(", ") || "aucune"}. Sorties ${cleanList(node.output_materials).join(", ") || "aucune"}.`);
    const kind = document.createElement("span");
    kind.className = "node-kind";
    kind.textContent = NODE_KINDS.find(([value]) => value === node.kind)?.[1] || node.kind;
    const name = document.createElement("span");
    name.className = "node-name";
    name.textContent = node.name;
    const inputs = document.createElement("span");
    inputs.className = "node-flow";
    inputs.textContent = `Entrée : ${cleanList(node.input_materials).join(", ") || "—"}`;
    const outputs = document.createElement("span");
    outputs.className = "node-flow";
    outputs.textContent = `Sortie : ${cleanList(node.output_materials).join(", ") || "—"}`;
    button.append(kind, name, inputs, outputs);
    button.addEventListener("click", () => selectNode(node.node_id));
    button.addEventListener("dblclick", () => openNodeDialog(node));
    button.addEventListener("pointerdown", beginNodeDrag);
    button.addEventListener("keydown", moveNodeWithKeyboard);
    nodeLayer.append(button);
  });
}

function edgeGeometry(edge) {
  const source = state.factory.process_graph.nodes.find((node) => node.node_id === edge.source);
  const target = state.factory.process_graph.nodes.find((node) => node.node_id === edge.target);
  if (!source || !target) return null;
  const x1 = source.position.x + NODE_WIDTH;
  const y1 = source.position.y + NODE_HEIGHT / 2;
  const x2 = target.position.x;
  const y2 = target.position.y + NODE_HEIGHT / 2;
  const bend = Math.max(45, Math.abs(x2 - x1) * .45);
  return {x1, y1, x2, y2, path: `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`};
}

function renderEdges() {
  edgeLayer.querySelectorAll(".rendered-edge").forEach((item) => item.remove());
  state.factory.process_graph.edges.forEach((edge, index) => {
    const geometry = edgeGeometry(edge);
    if (!geometry) return;
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", geometry.path);
    path.setAttribute("class", `edge-path rendered-edge${state.selectedEdge === index ? " selected" : ""}`);
    edgeLayer.append(path);
    if (edge.material || edge.condition) {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", String((geometry.x1 + geometry.x2) / 2));
      text.setAttribute("y", String((geometry.y1 + geometry.y2) / 2 - 8));
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("class", "edge-material rendered-edge");
      text.textContent = edge.material || edge.condition;
      edgeLayer.append(text);
    }
  });
}

function renderInspector() {
  const details = byId("selection-details");
  details.replaceChildren();
  if (state.selectedNode) {
    const node = state.factory.process_graph.nodes.find((item) => item.node_id === state.selectedNode);
    const heading = document.createElement("h3");
    heading.textContent = node.name;
    const body = document.createElement("p");
    body.textContent = `Entrées : ${cleanList(node.input_materials).join(", ") || "—"}\nSorties : ${cleanList(node.output_materials).join(", ") || "—"}\nMachines : ${node.machine_ids.join(", ") || "—"}`;
    body.style.whiteSpace = "pre-line";
    details.append(heading, body);
  } else if (state.selectedEdge !== null) {
    const edge = state.factory.process_graph.edges[state.selectedEdge];
    const body = document.createElement("p");
    body.textContent = `${edge.source} → ${edge.target}${edge.material ? `\nMatière : ${edge.material}` : ""}`;
    body.style.whiteSpace = "pre-line";
    details.append(body);
  } else {
    const body = document.createElement("p");
    body.className = "muted";
    body.textContent = "Sélectionnez une étape, une machine ou une relation.";
    details.append(body);
  }

  const edges = byId("edge-list");
  edges.replaceChildren();
  state.factory.process_graph.edges.forEach((edge, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${edge.source} → ${edge.target}${edge.material ? ` · ${edge.material}` : ""}`;
    button.addEventListener("click", () => {
      state.selectedEdge = index;
      state.selectedNode = null;
      render();
    });
    item.append(button);
    edges.append(item);
  });

  const machines = byId("machine-list");
  machines.replaceChildren();
  state.factory.machines.forEach((machine) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    const name = document.createElement("strong");
    name.textContent = machine.name;
    const density = document.createElement("span");
    density.className = "density";
    density.textContent = densityText(machine.machine_type);
    button.append(name, density);
    button.addEventListener("click", () => openMachineDialog(machine));
    item.append(button);
    machines.append(item);
  });
}

function selectNode(nodeId) {
  if (state.connectMode) {
    if (!state.connectSource) {
      state.connectSource = nodeId;
      status("Sélectionnez l'étape d'arrivée.");
    } else if (state.connectSource === nodeId) {
      status("Une étape ne peut pas être reliée à elle-même.", true);
    } else {
      const exists = state.factory.process_graph.edges.some((edge) => edge.source === state.connectSource && edge.target === nodeId);
      if (exists) status("Cette relation existe déjà.", true);
      else {
        const material = window.prompt("Matière transportée par cette relation (facultatif) :", "")?.trim();
        checkpoint();
        state.factory.process_graph.edges.push({schema_version: "1.0.0", provenance: "user-edited", source: state.connectSource, target: nodeId, ...(material ? {material} : {})});
        status(`Relation ${state.connectSource} → ${nodeId} créée.`);
      }
      state.connectSource = null;
      state.connectMode = false;
      byId("connect-mode").setAttribute("aria-pressed", "false");
    }
  }
  state.selectedNode = nodeId;
  state.selectedEdge = null;
  render();
}

function canvasPoint(event) {
  const rect = graphCanvas.getBoundingClientRect();
  return {x: Math.max(0, event.clientX - rect.left), y: Math.max(0, event.clientY - rect.top)};
}

function beginNodeDrag(event) {
  if (event.button !== 0 || state.connectMode) return;
  const node = state.factory.process_graph.nodes.find((item) => item.node_id === event.currentTarget.dataset.nodeId);
  checkpoint();
  state.drag = {node, startX: event.clientX, startY: event.clientY, x: node.position.x, y: node.position.y};
  event.currentTarget.setPointerCapture(event.pointerId);
}

document.addEventListener("pointermove", (event) => {
  if (!state.drag) return;
  state.drag.node.position.x = Math.max(0, Math.round(state.drag.x + event.clientX - state.drag.startX));
  state.drag.node.position.y = Math.max(0, Math.round(state.drag.y + event.clientY - state.drag.startY));
  const element = nodeLayer.querySelector(`[data-node-id="${CSS.escape(state.drag.node.node_id)}"]`);
  element.style.left = `${state.drag.node.position.x}px`;
  element.style.top = `${state.drag.node.position.y}px`;
  renderEdges();
});
document.addEventListener("pointerup", () => { state.drag = null; });

function moveNodeWithKeyboard(event) {
  if (!event.key.startsWith("Arrow")) return;
  event.preventDefault();
  checkpoint();
  const node = state.factory.process_graph.nodes.find((item) => item.node_id === event.currentTarget.dataset.nodeId);
  const step = event.shiftKey ? 20 : 4;
  if (event.key === "ArrowLeft") node.position.x = Math.max(0, node.position.x - step);
  if (event.key === "ArrowRight") node.position.x += step;
  if (event.key === "ArrowUp") node.position.y = Math.max(0, node.position.y - step);
  if (event.key === "ArrowDown") node.position.y += step;
  render();
  nodeLayer.querySelector(`[data-node-id="${CSS.escape(node.node_id)}"]`)?.focus();
}

function addNode(kind, position) {
  checkpoint();
  const prefix = kind.replace("quality_control", "qc");
  let index = 1;
  while (state.factory.process_graph.nodes.some((node) => node.node_id === `${prefix}-${index}`)) index += 1;
  const node = {
    schema_version: "1.0.0", provenance: "user-edited", node_id: `${prefix}-${index}`,
    kind, name: NODE_KINDS.find(([value]) => value === kind)?.[1] || kind,
    machine_ids: [], input_materials: [], output_materials: [],
    position: {x: Math.round(position.x), y: Math.round(position.y)},
  };
  state.factory.process_graph.nodes.push(node);
  state.selectedNode = node.node_id;
  state.armedKind = null;
  render();
  openNodeDialog(node, true);
}

graphCanvas.addEventListener("dragover", (event) => event.preventDefault());
graphCanvas.addEventListener("drop", (event) => {
  event.preventDefault();
  const kind = event.dataTransfer.getData("text/x-node-kind");
  if (NODE_KINDS.some(([value]) => value === kind)) addNode(kind, canvasPoint(event));
});
graphCanvas.addEventListener("click", (event) => {
  if (event.target !== graphCanvas && event.target !== nodeLayer && event.target !== edgeLayer) return;
  if (state.armedKind) addNode(state.armedKind, canvasPoint(event));
});

function openNodeDialog(node, isNew = false) {
  byId("node-dialog-title").textContent = isNew ? "Nouvelle étape" : "Modifier l'étape";
  byId("node-original-id").value = node.node_id;
  byId("node-id").value = node.node_id;
  byId("node-name").value = node.name;
  byId("node-kind").value = node.kind;
  byId("node-machines").value = node.machine_ids.join(", ");
  byId("node-inputs").value = cleanList(node.input_materials).join(", ");
  byId("node-outputs").value = cleanList(node.output_materials).join(", ");
  byId("node-capacity").value = node.capacity ?? "";
  byId("node-capacity-unit").value = node.capacity_unit ?? "";
  byId("node-error").textContent = "";
  byId("node-dialog").showModal();
}

byId("node-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const originalId = byId("node-original-id").value;
  const nodeId = byId("node-id").value.trim();
  const machines = cleanList(byId("node-machines").value);
  const node = state.factory.process_graph.nodes.find((item) => item.node_id === originalId);
  const duplicate = state.factory.process_graph.nodes.some((item) => item !== node && item.node_id === nodeId);
  const unknown = machines.filter((id) => !state.factory.machines.some((machine) => machine.machine_id === id));
  if (duplicate || unknown.length || (byId("node-kind").value === "operation" && !machines.length)) {
    byId("node-error").textContent = duplicate ? "Cet identifiant existe déjà." : unknown.length ? `Machines inconnues : ${unknown.join(", ")}` : "Une opération requiert au moins une machine.";
    return;
  }
  checkpoint();
  node.node_id = nodeId;
  node.name = byId("node-name").value.trim();
  node.kind = byId("node-kind").value;
  node.machine_ids = machines;
  node.input_materials = cleanList(byId("node-inputs").value);
  node.output_materials = cleanList(byId("node-outputs").value);
  const capacity = byId("node-capacity").value;
  const unit = byId("node-capacity-unit").value.trim();
  if (capacity && unit) { node.capacity = Number(capacity); node.capacity_unit = unit; }
  else { delete node.capacity; delete node.capacity_unit; }
  state.factory.process_graph.edges.forEach((edge) => {
    if (edge.source === originalId) edge.source = nodeId;
    if (edge.target === originalId) edge.target = nodeId;
  });
  state.selectedNode = nodeId;
  byId("node-dialog").close();
  status(`Étape ${node.name} enregistrée.`);
  render();
});

function populateMachineTypes(selected = "") {
  const select = byId("machine-type");
  select.replaceChildren();
  state.factory.machine_types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type.machine_type;
    option.textContent = type.name;
    option.selected = type.machine_type === selected;
    select.append(option);
  });
  updateDensityPreview();
}

function updateDensityPreview() {
  byId("failure-density").textContent = densityText(byId("machine-type").value);
}

function openMachineDialog(machine = null) {
  populateMachineTypes(machine?.machine_type);
  byId("machine-original-id").value = machine?.machine_id || "";
  byId("machine-id").value = machine?.machine_id || "";
  byId("machine-name").value = machine?.name || "";
  byId("machine-capacity").value = machine?.capacity_per_hour || "";
  byId("machine-unit").value = machine?.capacity_unit || "tonnes/hour";
  byId("machine-availability").value = machine?.availability || .95;
  byId("machine-capabilities").value = cleanList(machine?.capabilities).join(", ");
  byId("machine-error").textContent = "";
  byId("delete-machine").hidden = !machine;
  byId("machine-dialog").showModal();
}

byId("machine-type").addEventListener("change", updateDensityPreview);
byId("machine-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const originalId = byId("machine-original-id").value;
  const machineId = byId("machine-id").value.trim();
  let machine = state.factory.machines.find((item) => item.machine_id === originalId);
  if (state.factory.machines.some((item) => item !== machine && item.machine_id === machineId)) {
    byId("machine-error").textContent = "Cet identifiant existe déjà.";
    return;
  }
  checkpoint();
  const record = {
    schema_version: "1.0.0", provenance: "user-edited", machine_id: machineId,
    name: byId("machine-name").value.trim(), machine_type: byId("machine-type").value,
    capabilities: cleanList(byId("machine-capabilities").value),
    capacity_per_hour: Number(byId("machine-capacity").value), capacity_unit: byId("machine-unit").value.trim(),
    availability: Number(byId("machine-availability").value), metadata: machine?.metadata || {},
  };
  if (machine) Object.assign(machine, record);
  else { machine = record; state.factory.machines.push(machine); }
  if (originalId && originalId !== machineId) state.factory.process_graph.nodes.forEach((node) => { node.machine_ids = node.machine_ids.map((id) => id === originalId ? machineId : id); });
  byId("machine-dialog").close();
  status(`Machine ${machine.name} enregistrée.`);
  render();
});

function openTypeDialog() {
  const select = byId("type-id");
  select.replaceChildren();
  state.factory.machine_types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type.machine_type;
    option.textContent = type.name;
    select.append(option);
  });
  loadSelectedType();
  byId("type-dialog").showModal();
}

function loadSelectedType() {
  const type = state.factory.machine_types.find((item) => item.machine_type === byId("type-id").value);
  if (!type) return;
  byId("type-name").value = type.name;
  byId("type-shape").value = type.failure_density.shape;
  byId("type-scale").value = type.failure_density.scale_hours;
}
byId("type-id").addEventListener("change", loadSelectedType);
byId("type-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const type = state.factory.machine_types.find((item) => item.machine_type === byId("type-id").value);
  checkpoint();
  type.name = byId("type-name").value.trim();
  type.failure_density = {family: "weibull", shape: Number(byId("type-shape").value), scale_hours: Number(byId("type-scale").value)};
  byId("type-dialog").close();
  status(`Densité ${type.name} enregistrée.`);
  render();
});

function deleteSelected() {
  if (state.selectedEdge !== null) {
    const edge = state.factory.process_graph.edges[state.selectedEdge];
    if (!window.confirm(`Supprimer la relation ${edge.source} → ${edge.target} ?`)) return;
    checkpoint();
    state.factory.process_graph.edges.splice(state.selectedEdge, 1);
    state.selectedEdge = null;
    status("Relation supprimée.");
  } else if (state.selectedNode) {
    const node = state.factory.process_graph.nodes.find((item) => item.node_id === state.selectedNode);
    if (!window.confirm(`Supprimer l'étape ${node.name} et ses relations ?`)) return;
    checkpoint();
    state.factory.process_graph.nodes = state.factory.process_graph.nodes.filter((item) => item !== node);
    state.factory.process_graph.edges = state.factory.process_graph.edges.filter((edge) => edge.source !== node.node_id && edge.target !== node.node_id);
    state.selectedNode = null;
    status("Étape et relations associées supprimées.");
  }
  render();
}

function duplicateSelected() {
  const source = state.factory.process_graph.nodes.find((item) => item.node_id === state.selectedNode);
  if (!source) return;
  checkpoint();
  let index = 2;
  let nodeId = `${source.node_id}-copy`;
  while (state.factory.process_graph.nodes.some((node) => node.node_id === nodeId)) nodeId = `${source.node_id}-copy-${index++}`;
  const copy = JSON.parse(JSON.stringify(source));
  copy.node_id = nodeId;
  copy.name = `${source.name} (copie)`;
  copy.position = {x: source.position.x + 40, y: source.position.y + 140};
  state.factory.process_graph.nodes.push(copy);
  state.selectedNode = nodeId;
  status(`Étape ${copy.name} dupliquée; ses relations restent à créer.`);
  render();
}

function autoLayout() {
  checkpoint();
  const nodes = state.factory.process_graph.nodes;
  const known = new Set(nodes.map((node) => node.node_id));
  const indegree = new Map(nodes.map((node) => [node.node_id, 0]));
  state.factory.process_graph.edges.forEach((edge) => {
    if (known.has(edge.source) && known.has(edge.target)) indegree.set(edge.target, indegree.get(edge.target) + 1);
  });
  const level = new Map();
  const queue = nodes.filter((node) => indegree.get(node.node_id) === 0).map((node) => node.node_id);
  queue.forEach((id) => level.set(id, 0));
  for (let index = 0; index < queue.length; index += 1) {
    const source = queue[index];
    state.factory.process_graph.edges.filter((edge) => edge.source === source).forEach((edge) => {
      level.set(edge.target, Math.max(level.get(edge.target) || 0, (level.get(source) || 0) + 1));
      indegree.set(edge.target, indegree.get(edge.target) - 1);
      if (indegree.get(edge.target) === 0) queue.push(edge.target);
    });
  }
  nodes.forEach((node) => { if (!level.has(node.node_id)) level.set(node.node_id, 0); });
  const rows = new Map();
  nodes.forEach((node) => {
    const column = level.get(node.node_id);
    const row = rows.get(column) || 0;
    node.position = {x: 60 + column * 250, y: 70 + row * 165};
    rows.set(column, row + 1);
  });
  status("Graphe auto-agencé par niveau de dépendance.");
  render();
}

function deleteMachine() {
  const machineId = byId("machine-original-id").value;
  const usedBy = state.factory.process_graph.nodes.filter((node) => node.machine_ids.includes(machineId));
  if (usedBy.length) {
    byId("machine-error").textContent = `Machine encore utilisée par : ${usedBy.map((node) => node.name).join(", ")}. Modifiez d'abord ces étapes.`;
    return;
  }
  const machine = state.factory.machines.find((item) => item.machine_id === machineId);
  if (!machine || !window.confirm(`Supprimer la machine ${machine.name} ?`)) return;
  checkpoint();
  state.factory.machines = state.factory.machines.filter((item) => item !== machine);
  byId("machine-dialog").close();
  status(`Machine ${machine.name} supprimée.`);
  render();
}

function exportJson() {
  const errors = validateFactory();
  if (errors.length) { status(`Export bloqué : ${errors[0]}`, true); return; }
  const blob = new Blob([JSON.stringify(state.factory, null, 2) + "\n"], {type: "application/json"});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${state.factory.factory_id || "factory"}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
  status("JSON compatible FactoryConfig exporté.");
}

byId("import-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const imported = normalizeFactory(JSON.parse(await file.text()));
    const errors = validateFactory(imported);
    if (errors.length) throw new Error(errors.join(" ; "));
    state.factory = imported;
    state.history = [];
    state.future = [];
    state.validatedSnapshot = null;
    state.selectedNode = null;
    state.selectedEdge = null;
    render();
    status(`${file.name} importé et validé.`);
  } catch (error) { status(`Import refusé : ${error.message}`, true); }
  event.target.value = "";
});
byId("export-json").addEventListener("click", exportJson);
byId("validate").addEventListener("click", () => {
  const errors = validateFactory();
  state.validatedSnapshot = errors.length ? null : serialise();
  byId("write-config").disabled = Boolean(errors.length);
  status(errors.length ? `${errors.length} erreur(s) : ${errors.join(" ; ")}` : "Configuration valide, prête à exporter.", Boolean(errors.length));
});
byId("write-config").addEventListener("click", async () => {
  if (!state.validatedSnapshot || state.validatedSnapshot !== serialise()) {
    status("Validez de nouveau la configuration avant l'écriture.", true);
    return;
  }
  if (!window.confirm("Écrire cette configuration validée dans le fichier chargé par le serveur local ?")) return;
  try {
    const response = await fetch("factory.json", {method: "POST", headers: {"Content-Type": "application/json"}, body: serialise()});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
    status(`Configuration écrite explicitement dans ${result.path}.`);
    byId("write-config").disabled = true;
  } catch (error) { status(`Écriture refusée : ${error.message}`, true); }
});
byId("connect-mode").addEventListener("click", (event) => {
  state.connectMode = !state.connectMode;
  state.connectSource = null;
  event.currentTarget.setAttribute("aria-pressed", String(state.connectMode));
  status(state.connectMode ? "Sélectionnez l'étape de départ." : "Création de relation annulée.");
  render();
});
byId("edit-selected").addEventListener("click", () => openNodeDialog(state.factory.process_graph.nodes.find((item) => item.node_id === state.selectedNode)));
byId("delete-selected").addEventListener("click", deleteSelected);
byId("duplicate-selected").addEventListener("click", duplicateSelected);
byId("auto-layout").addEventListener("click", autoLayout);
byId("undo").addEventListener("click", undo);
byId("redo").addEventListener("click", redo);
byId("add-machine").addEventListener("click", () => openMachineDialog());
byId("edit-machine-types").addEventListener("click", openTypeDialog);
byId("delete-machine").addEventListener("click", deleteMachine);
document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => byId(button.dataset.close).close()));
document.addEventListener("keydown", (event) => {
  if (event.key === "Delete" && !document.querySelector("dialog[open]") && (state.selectedNode || state.selectedEdge !== null)) deleteSelected();
  if (event.key === "Escape" && state.connectMode) {
    state.connectMode = false; state.connectSource = null; byId("connect-mode").setAttribute("aria-pressed", "false"); render();
  }
});

async function start() {
  try {
    const response = await fetch("factory.json", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.factory = normalizeFactory(await response.json());
    const errors = validateFactory();
    if (errors.length) throw new Error(errors.join(" ; "));
    render();
    status("Configuration chargée. Les positions sont enregistrées dans chaque étape.");
  } catch (error) {
    status(`Chargement impossible : ${error.message}. Lancez l'éditeur avec python -m sylvapapers_digital_twin.web.`, true);
  }
}

start();
