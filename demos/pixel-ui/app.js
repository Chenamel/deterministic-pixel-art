const $ = (selector) => document.querySelector(selector);
const stateNames = ['normal', 'hover', 'focus', 'pressed', 'selected', 'disabled'];
const controlIds = ['run', 'loop', 'export'];
let manifest, assets, revision = 'revised', runCount = 0, selected = false;
const interaction = new Map(controlIds.map(id => [id, {hover: false, pressed: false}]));
const actions = [];

async function bytes(path, expected) {
  const response = await fetch(path, {cache: 'no-store'});
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  const data = await response.arrayBuffer();
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
    .map(value => value.toString(16).padStart(2, '0')).join('');
  if (expected && hash !== expected) throw new Error(`${path}: asset hash mismatch; rebuild/reload the complete set`);
  return data;
}

async function loadAsset(path, type) {
  const data = await bytes(`assets/${path}`, manifest.assets[path].sha256);
  return type === 'image' ? createImageBitmap(new Blob([data], {type: 'image/png'}))
    : JSON.parse(new TextDecoder().decode(data));
}

async function loadVariant(name) {
  const [image, layout, context] = await Promise.all([
    loadAsset(`${name}/buttons.png`, 'image'), loadAsset(`${name}/layout.json`), loadAsset(`${name}/context.json`)]);
  const config = manifest.variants[name];
  if (image.width !== config.width * 3 || image.height !== 36 ||
      JSON.stringify(layout.atlas.cells.map(cell => cell.name)) !== JSON.stringify(stateNames))
    throw new Error(`${name}: texture dimensions or state order differ from the consumer contract`);
  return {image, layout, context};
}

function labelGeometry(ctx, state, label) {
  const cell = assets[revision].layout.atlas.cells.find(cell => cell.name === state);
  const reserved = assets[revision].context.regions.find(region => region.name === `${state}-text`).rect;
  const region = [reserved[0] - cell.x, reserved[1] - cell.y, reserved[2], reserved[3]];
  ctx.font = '8px PixelDemo'; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  const measure = ctx.measureText(label);
  const x = Math.round(region[0] + (region[2] - measure.width) / 2);
  const y = Math.round(region[1] + (region[3] + measure.actualBoundingBoxAscent - measure.actualBoundingBoxDescent) / 2)
    + (state === 'pressed' ? 1 : 0);
  const bounds = [x - measure.actualBoundingBoxLeft, y - measure.actualBoundingBoxAscent,
    measure.actualBoundingBoxLeft + measure.actualBoundingBoxRight,
    measure.actualBoundingBoxAscent + measure.actualBoundingBoxDescent];
  const fits = bounds[0] >= region[0] && bounds[1] >= region[1] &&
    bounds[0] + bounds[2] <= region[0] + region[2] && bounds[1] + bounds[3] <= region[1] + region[3];
  return {state, label, region, bounds, fits, x, y, advance: measure.width};
}

function draw(canvas, state, label) {
  const {image, layout} = assets[revision];
  const cell = layout.atlas.cells.find(cell => cell.name === state);
  canvas.width = cell.w; canvas.height = cell.h;
  const ctx = canvas.getContext('2d'); ctx.imageSmoothingEnabled = false;
  ctx.drawImage(image, cell.x, cell.y, cell.w, cell.h, 0, 0, cell.w, cell.h);
  const text = labelGeometry(ctx, state, label);
  ctx.fillStyle = state === 'disabled' ? '#8997A5' : '#E5ECEE';
  ctx.fillText(label, text.x, text.y);
  return text;
}

function currentState(id) {
  const button = $(`#${id}`), activity = interaction.get(id);
  if (button.disabled) return 'disabled';
  if (activity.pressed) return 'pressed';
  // Focus is also a separate DOM outline, preserving the selected check/underline.
  if (id === 'loop' && selected) return 'selected';
  if (button.matches(':focus-visible')) return 'focus';
  return activity.hover ? 'hover' : 'normal';
}

function refresh() {
  if (!assets) return;
  for (const id of controlIds) {
    const button = $(`#${id}`), state = currentState(id);
    button.dataset.state = state;
    draw(button.querySelector('canvas'), state, manifest.labels[id]);
  }
  $('#selection').textContent = `Loop is ${selected ? 'on' : 'off'}`;
  const probe = document.createElement('canvas').getContext('2d');
  const text = stateNames.flatMap(state => Object.values(manifest.labels).map(label => labelGeometry(probe, state, label)));
  const failures = text.filter(item => !item.fits);
  const report = {
    ready: true, revision, scale: Number($('#scale').value), background: $('#theme').value,
    font: {family: 'Silkscreen Regular', cssFamily: 'PixelDemo', size: 8,
      loaded: document.fonts.check('8px PixelDemo'), sha256: manifest.font.sha256},
    texture: {width: assets[revision].image.width, height: assets[revision].image.height,
      cellWidth: manifest.variants[revision].width, cellHeight: 18, hashVerified: true, namedLayoutVerified: true},
    textFits: failures.length === 0, textFailures: failures, textChecks: text,
    controls: controlIds.map(id => ({id, state: currentState(id), disabled: $(`#${id}`).disabled,
      selected: $(`#${id}`).getAttribute('aria-pressed'),
      cssSize: [$(`#${id}`).getBoundingClientRect().width, $(`#${id}`).getBoundingClientRect().height]})),
    runCount, actions, scope: 'Actual browser/loaded-font checks; no in-game acceptance or aesthetic score.'
  };
  $('#checks').textContent = JSON.stringify(report, null, 2);
  $('#fit-status').dataset.valid = String(report.textFits);
  $('#fit-status').textContent = report.textFits ? 'Text fits every reserved region in all six states.'
    : `Text needs more room: ${[...new Set(failures.map(item => item.label))].join(', ')}. Compare the revised asset.`;
}

function gallery() {
  $('#states').replaceChildren(...stateNames.map(state => {
    const card = document.createElement('div'), label = document.createElement('span'), canvas = document.createElement('canvas');
    label.className = 'state-name'; label.textContent = state;
    canvas.setAttribute('role', 'img'); canvas.setAttribute('aria-label', `${state} button: ${manifest.labels.run}`);
    card.append(label, canvas); draw(canvas, state, manifest.labels.run); return card;
  }));
}

function connectControls() {
  for (const id of controlIds) {
    const button = $(`#${id}`), activity = interaction.get(id);
    button.setAttribute('aria-label', manifest.labels[id]);
    button.addEventListener('pointerenter', () => {activity.hover = true; refresh();});
    button.addEventListener('pointerleave', () => {activity.hover = false; activity.pressed = false; refresh();});
    button.addEventListener('pointerdown', event => {if (event.button === 0 && !button.disabled) {activity.pressed = true; refresh();}});
    button.addEventListener('keydown', event => {if ([' ', 'Enter'].includes(event.key)) {activity.pressed = true; refresh();}});
    button.addEventListener('keyup', () => {activity.pressed = false; refresh();});
    button.addEventListener('focus', refresh);
    button.addEventListener('blur', () => {activity.pressed = false; refresh();});
  }
  document.addEventListener('pointerup', () => {interaction.forEach(value => value.pressed = false); refresh();});
  document.addEventListener('pointercancel', () => {interaction.forEach(value => value.pressed = false); refresh();});
  $('#run').addEventListener('click', () => {
    runCount++; actions.push({control: 'run', count: runCount});
    $('#activity').textContent = `Run ${runCount} started`; refresh();
  });
  $('#loop').addEventListener('click', () => {
    selected = !selected; $('#loop').setAttribute('aria-pressed', String(selected));
    actions.push({control: 'loop', selected});
    $('#activity').textContent = selected ? 'Loop enabled' : 'Loop disabled'; refresh();
  });
  $('#scale').addEventListener('change', () => {
    document.documentElement.style.setProperty('--scale', $('#scale').value); refresh();
  });
  $('#theme').addEventListener('change', () => {document.body.dataset.theme = $('#theme').value; refresh();});
  $('#revision').addEventListener('change', () => {
    revision = $('#revision').value;
    document.documentElement.style.setProperty('--button-width', manifest.variants[revision].width);
    gallery(); refresh();
  });
}

async function start() {
  $('#run').disabled = true; $('#loop').disabled = true;
  manifest = JSON.parse(new TextDecoder().decode(await bytes('assets/manifest.json')));
  await bytes('fonts/Silkscreen-Regular.ttf', manifest.font.sha256);
  const loaded = await document.fonts.load('8px PixelDemo');
  if (loaded.length !== 1 || loaded[0].status !== 'loaded') throw new Error('Bundled font did not load; fallback fonts do not establish text fit');
  const [baseline, revised, courier] = await Promise.all([
    loadVariant('baseline'), loadVariant('revised'), bytes('assets/courier.png', manifest.assets['courier.png'].sha256)]);
  const courierUrl = URL.createObjectURL(new Blob([courier], {type: 'image/png'}));
  $('#courier').src = courierUrl;
  try { await $('#courier').decode(); } finally { URL.revokeObjectURL(courierUrl); }
  assets = {baseline, revised};
  for (const option of $('#revision').options) {
    const name = option.value;
    option.textContent = `${name === 'baseline' ? 'Baseline' : 'Revised'} · ${manifest.variants[name].width} px`;
  }
  revision = $('#revision').value;
  document.documentElement.style.setProperty('--button-width', manifest.variants[revision].width);
  document.documentElement.style.setProperty('--scale', $('#scale').value);
  document.body.dataset.theme = $('#theme').value;
  $('#run').disabled = false; $('#loop').disabled = false;
  $('#activity').textContent = 'Ready';
  document.body.dataset.ready = 'true';
  connectControls(); gallery(); refresh();
}

start().catch(error => {
  $('#error').hidden = false; $('#error').textContent = error.message;
  $('#checks').textContent = JSON.stringify({ready: false, error: error.message});
});
