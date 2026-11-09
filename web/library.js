const el = id => document.getElementById(id);
let ownerCode = '', currentMaterial = null, currentPassage = null;
function say(message) { el('library-status').textContent = message; el('review-status').textContent = message; el('review-status').hidden = !currentMaterial; }
async function api(path, data) {
  const options = {headers: {'X-Piet-Owner': ownerCode}};
  if (data !== undefined) { options.method = 'POST'; options.headers['Content-Type'] = 'application/json'; options.body = JSON.stringify(data); }
  const response = await fetch(path, options); const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The library could not finish this action.');
  return result;
}
function node(tag, text, className) { const element = document.createElement(tag); element.textContent = text; if (className) element.className = className; return element; }
async function refreshLibrary() {
  const result = await api('/api/library');
  el('material-list').replaceChildren(); el('empty-library').hidden = result.materials.length > 0;
  for (const material of result.materials) {
    const button = node('button', '', 'material-item secondary');
    button.append(node('strong', material.metadata.title), node('span', `${material.metadata.grade} · ${material.metadata.subject} · ${material.metadata.language}`), node('span', `${material.approved} of ${material.total} passages approved`));
    button.onclick = async () => { try { showMaterial(await api('/api/library/' + material.id)); } catch (error) { say(error.message); } };
    el('material-list').append(button);
  }
}
el('unlock').onsubmit = async event => {
  event.preventDefault(); ownerCode = el('owner-code').value.trim();
  try { await refreshLibrary(); el('unlock-card').hidden = true; el('owner-space').hidden = false; el('owner-code').value = ''; say('Library unlocked. New material is added as drafts.'); }
  catch (error) { ownerCode = ''; say(error.message); }
};
el('lock').onclick = () => {
  ownerCode = ''; currentMaterial = null; currentPassage = null;
  el('owner-space').hidden = true; el('unlock-card').hidden = false; el('review-card').hidden = true;
  el('material-list').replaceChildren(); el('passage-text').value = ''; el('original-text').textContent = '';
  el('passage-select').replaceChildren(); el('review-title').textContent = ''; el('review-meta').textContent = '';
  el('manual-text').value = ''; el('reviewer').value = ''; say('Library locked.');
};
el('refresh-library').onclick = async () => { try { await refreshLibrary(); if (currentMaterial) showMaterial(await api('/api/library/' + currentMaterial.id)); say('Library refreshed.'); } catch (error) { say(error.message); } };
el('book-file').onchange = () => { const file = el('book-file').files[0]; if (file && !el('book-title').value) el('book-title').value = file.name.replace(/\.[^.]+$/, ''); };
function base64(file) {
  return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onerror = () => reject(new Error('This file could not be read.')); reader.onload = () => resolve(String(reader.result).split(',')[1]); reader.readAsDataURL(file); });
}
el('import-form').onsubmit = async event => {
  event.preventDefault(); const file = el('book-file').files[0];
  if (!file || file.size === 0 || file.size > 20 * 1024 * 1024) return say('Choose a nonempty file of up to 20 MB.');
  el('import-button').disabled = true; say('Adding your material and extracting its text. It will stay in draft for review.');
  try {
    const metadata = {};
    for (const field of ['title', 'provider', 'framework', 'grade', 'subject', 'language', 'edition']) metadata[field] = el('book-' + field).value.trim();
    metadata.permission = el('permission').checked;
    const result = await api('/api/library/import', {filename: file.name, content: await base64(file), metadata});
    await refreshLibrary(); showMaterial(result); say(`Added “${result.metadata.title}”. Review and approve each suitable passage before it appears for learners.`);
    el('book-file').value = ''; el('book-title').value = ''; el('permission').checked = false;
  } catch (error) { say(error.message); }
  finally { el('import-button').disabled = false; }
};
function showMaterial(material, selectedId) {
  currentMaterial = material; el('review-card').hidden = false;
  el('review-title').textContent = material.metadata.title;
  el('review-meta').textContent = `${material.metadata.provider} · ${material.metadata.framework} · ${material.metadata.grade} · ${material.metadata.subject} · ${material.metadata.language} · ${material.metadata.edition}`;
  el('warnings').replaceChildren(...material.warnings.map(warning => node('p', warning, 'notice')));
  el('passage-select').replaceChildren();
  for (const passage of material.passages) { const option = node('option', `${passage.location} — ${passage.status}`); option.value = passage.id; el('passage-select').append(option); }
  if (selectedId && material.passages.some(x => x.id === selectedId)) el('passage-select').value = selectedId;
  el('review-form').hidden = material.passages.length === 0;
  el('passage-select').disabled = material.passages.length === 0;
  if (!material.passages.length) el('warnings').append(node('p', 'No text passages were extracted. Add a transcription manually below, or use a text-based copy.', 'notice'));
  selectPassage();
}
function selectPassage() {
  currentPassage = currentMaterial.passages.find(x => x.id === el('passage-select').value);
  if (!currentPassage) return;
  el('passage-text').value = currentPassage.text;
  el('original-text').textContent = currentPassage.original_text || 'Manually entered passage. Compare it with the original document.';
  el('passage-state').textContent = `${currentPassage.location} · ${currentPassage.status}${currentPassage.reviewed_by ? ' · Last reviewed by ' + currentPassage.reviewed_by : ''}`;
  for (const input of document.querySelectorAll('[name="age-band"]')) input.checked = currentPassage.age_bands.includes(input.value);
  el('review-confirm').checked = false;
}
el('passage-select').onchange = selectPassage;
el('passage-text').oninput = () => { el('review-confirm').checked = false; };
for (const input of document.querySelectorAll('[name="age-band"]')) input.onchange = () => { el('review-confirm').checked = false; };
async function review(status) {
  if (!currentPassage) return;
  const age_bands = [...document.querySelectorAll('[name="age-band"]:checked')].map(x => x.value);
  if (status === 'approved' && (!age_bands.length || !el('review-confirm').checked)) return say('Choose suitable age groups and confirm your review before approving.');
  el('approve').disabled = true; el('save-draft').disabled = true;
  try {
    const id = currentPassage.id;
    const result = await api('/api/library/passages/' + id + '/review', {text: el('passage-text').value, age_bands, reviewed_by: el('reviewer').value, status, revision: currentPassage.revision, confirmed: el('review-confirm').checked});
    showMaterial(result, id); await refreshLibrary();
    say(status === 'approved' ? 'Passage approved for the selected ages. Refresh the reading space to see it.' : 'Saved as draft. This passage is unavailable for new learner questions.');
  } catch (error) { say(error.message); }
  finally { el('approve').disabled = false; el('save-draft').disabled = false; }
}
el('review-form').onsubmit = event => { event.preventDefault(); review('approved'); };
el('save-draft').onclick = () => { if (el('review-form').reportValidity()) review('draft'); };
el('manual-form').onsubmit = async event => {
  event.preventDefault(); el('manual-button').disabled = true;
  try {
    const result = await api('/api/library/' + currentMaterial.id + '/passages', {location: el('manual-location').value, text: el('manual-text').value});
    showMaterial(result, result.passages[result.passages.length - 1].id); await refreshLibrary();
    el('manual-text').value = ''; el('manual-location').value = ''; say('Manual passage added as draft. Review it before approval.');
  } catch (error) { say(error.message); }
  finally { el('manual-button').disabled = false; }
};
el('download-original').onclick = async () => {
  try {
    const response = await fetch('/api/library/' + currentMaterial.id + '/original', {headers: {'X-Piet-Owner': ownerCode}});
    if (!response.ok) throw new Error('The original file could not be opened.');
    const url = URL.createObjectURL(await response.blob()); const link = document.createElement('a');
    link.href = url; link.download = currentMaterial.filename; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 10000);
  } catch (error) { say(error.message); }
};
