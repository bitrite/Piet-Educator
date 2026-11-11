/* Study quests use the same source and age boundaries as the reader. */
const studyEl = id => document.getElementById(id);
const studyState = window.PietStudyState;
let practice = studyState.empty(), quest = null, stage = '', paused = false, studyBusy = false, storageKey = '', studyScope = '';
const badgeText = {tried: 'Tried an idea', help: 'Asked for support', reflected: 'Reflected on learning', another: 'Tried another explanation'};
function studySay(text) { studyEl('study-status').textContent = text; }
function studySave() {
  if (!storageKey) return false;
  try {
    if (studyEl('study-save').checked) localStorage.setItem(storageKey, JSON.stringify(practice));
    else localStorage.removeItem(storageKey);
    return true;
  } catch (_) { studyEl('study-save').checked = false; studySay('Browser storage could not be changed. You can practise in memory; use browser site-data controls if you need to remove an earlier saved record.'); return false; }
}
function studySavePreferences() {
  if (!studyScope) return;
  try { localStorage.setItem('piet-study-preferences-v1:' + studyScope, JSON.stringify({rewards: studyEl('study-rewards').checked, celebration: studyEl('study-celebration').value})); } catch (_) {}
}
function studyRenderProgress() {
  const enabled = studyEl('study-rewards').checked;
  studyEl('study-progress').hidden = !enabled;
  studyEl('study-total').textContent = practice.completed ? `${practice.completed} study ${practice.completed === 1 ? 'activity explored' : 'activities explored'}. Participation, not a test score.` : 'No practice recorded this visit. Start whenever you choose.';
  studyEl('study-badges').replaceChildren();
  for (const badge of practice.badges) { const li = document.createElement('li'); li.textContent = badgeText[badge]; studyEl('study-badges').append(li); }
  const garden = studyEl('study-garden'); garden.hidden = studyEl('study-celebration').value !== 'garden'; garden.replaceChildren();
  for (let i = 0; i < Math.min(practice.completed, 6); i++) { const plant = document.createElement('span'); plant.className = 'study-plant'; garden.append(plant); }
  studyEl('study-reviews').replaceChildren();
  studyEl('study-review-empty').hidden = practice.reviews.length > 0;
  for (const review of practice.reviews) {
    const lesson = session.lessons.find(x => x.id === review.lesson_id); if (!lesson) continue;
    const button = document.createElement('button'); button.className = 'secondary material-item';
    const title = document.createElement('strong'); title.textContent = lesson.title;
    const when = document.createElement('span'); when.textContent = review.due <= Date.now() ? 'Available to revisit whenever you choose' : 'You chose a review around ' + new Date(review.due).toLocaleDateString();
    button.append(title, when); button.onclick = () => {
      if (studyBusy) return;
      studyEl('material').value = lesson.material_id || 'samples'; fillPassages();
      studyEl('lesson').value = lesson.id; chooseLesson(); studyEl('study-method').value = 'review';
      studySay('This idea is ready to revisit. Start when you choose.'); studyEl('study-start').focus();
    };
    studyEl('study-reviews').append(button);
  }
}
function studySetStage(next) {
  stage = next;
  for (const name of ['explore', 'try', 'reflect']) {
    const step = studyEl('step-' + name);
    if (name === stage) step.setAttribute('aria-current', 'step'); else step.removeAttribute('aria-current');
  }
  studyEl('study-ready').hidden = next !== 'explore';
  studyEl('study-practice').hidden = next === 'explore';
  studyEl('study-reflection').hidden = next !== 'reflect';
}
function studyReset(message = '') {
  stopReading(); quest = null; stage = ''; paused = false;
  studyEl('passage').hidden = false; studyEl('study-cover').checked = false;
  studyEl('study-quest').hidden = true; studyEl('study-pause').hidden = true;
  studyEl('study-celebrate').hidden = true; studyEl('study-pause').textContent = 'Take a break';
  studyEl('study-attempt').value = ''; studyEl('study-feedback').textContent = '';
  studyEl('study-quote').hidden = true; studyEl('study-hint-text').hidden = true;
  studyEl('study-hint-text').textContent = ''; studyEl('study-reflect').value = 'tried'; studyEl('study-review-days').value = '0';
  if (message) studySay(message);
}
function studyLoaded() {
  const scope = session.instance_id + ':' + session.age_band;
  if (scope !== studyScope) {
    studyScope = scope; storageKey = 'piet-practice-v1:' + scope; practice = studyState.empty(); studyEl('study-save').checked = false;
    try { const saved = localStorage.getItem(storageKey); if (saved) { practice = studyState.sanitize(JSON.parse(saved), session.study_source_versions); studyEl('study-save').checked = true; } } catch (_) {}
    studyEl('study-celebration').value = session.age_band === 'adult' ? 'quiet' : 'garden';
    studyEl('study-rewards').checked = true;
    try {
      const prefs = JSON.parse(localStorage.getItem('piet-study-preferences-v1:' + scope) || '{}');
      if (typeof prefs.rewards === 'boolean') studyEl('study-rewards').checked = prefs.rewards;
      if (['message', 'garden', 'quiet'].includes(prefs.celebration)) studyEl('study-celebration').value = prefs.celebration;
    } catch (_) {}
    studyEl('study-title').textContent = session.age_band === 'adult' ? 'A focused study session' : 'A small study quest';
    studyEl('study-start').textContent = session.age_band === 'adult' ? 'Start a study session' : 'Start a small quest';
    studyEl('study-finish').textContent = session.age_band === 'adult' ? 'Finish this session' : 'Finish this quest';
  }
  practice = studyState.sanitize(practice, session.study_source_versions); studySave(); studyRenderProgress();
}
function studySetBusy(value) {
  studyBusy = value;
  for (const id of ['study-start', 'study-submit', 'study-hint', 'study-reveal', 'study-ready', 'study-finish', 'study-pause', 'study-method', 'study-challenge', 'material', 'lesson', 'refresh-reading', 'explain', 'again']) studyEl(id).disabled = value;
}
async function studyApi(path, body) {
  const response = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Piet-Token': session.token}, body: JSON.stringify(body)});
  const result = await response.json(); if (!response.ok) throw new Error(result.error || 'This activity could not finish. Start again when ready.'); return result;
}
studyEl('study-start').onclick = async () => {
  if (!activeLesson || studyBusy) return;
  studyReset(); studySetBusy(true); studySay('Preparing and checking one small activity. Your passage is still available.');
  try {
    const result = await studyApi('/api/study/create', {lesson_id: activeLesson.id, method: studyEl('study-method').value, challenge: studyEl('study-challenge').value});
    if (result.status !== 'checked') return studySay(result.answer);
    if (result.source_fingerprint !== session.study_source_versions[activeLesson.id]) return studySay('This passage changed since it was opened. Refresh the reading library before starting a quest.');
    quest = {...result, lesson_id: activeLesson.id};
    studyEl('study-instruction').textContent = result.instruction; studyEl('study-example').textContent = result.worked_example;
    studyEl('study-example').hidden = !result.worked_example;
    studyEl('study-question').textContent = result.question;
    studyEl('study-quest').hidden = false; studyEl('study-pause').hidden = false;
    studySetStage('explore'); studySay('Explore the passage and any example first. There is no timer.');
  } catch (error) { studySay(error.message); } finally { studySetBusy(false); }
};
studyEl('study-ready').onclick = () => { studySetStage('try'); studySay('Try the question, ask for a hint or choose Show me. Each is a valid way to participate.'); };
studyEl('study-cover').onchange = () => { stopReading(); studyEl('passage').hidden = studyEl('study-cover').checked; };
studyEl('study-pause').onclick = () => {
  if (!quest) return; stopReading(); paused = !paused; studyEl('study-quest').hidden = paused;
  studyEl('passage').hidden = false; studyEl('study-cover').checked = false;
  studyEl('study-pause').textContent = paused ? 'Resume when ready' : 'Take a break';
  studySay(paused ? 'Take the time you need. No points or progress are lost. This activity stays in memory for this visit and may need restarting after a long break.' : 'Welcome back. Continue at your own pace.');
};
async function studyAct(action) {
  if (!quest || studyBusy) return;
  studySetBusy(true); studySay(action === 'respond' ? 'Exploring your meaning and checking the feedback. Spelling is not graded.' : 'Opening checked support. Using help never reduces progress.');
  try {
    const body = {activity_id: quest.activity_id, action}; if (action === 'respond') body.attempt = studyEl('study-attempt').value;
    const result = await studyApi('/api/study/action', body);
    if (result.status !== 'checked') { studySay(result.answer); return; }
    if (action === 'hint') {
      studyEl('study-hint-text').textContent = result.answer; studyEl('study-hint-text').hidden = false;
    } else {
      studyEl('study-feedback').textContent = result.answer; studyEl('study-quote').textContent = result.quote ? (result.quote_kind === 'practice' ? 'Checked practice reference: “' : 'From the passage: “') + result.quote + '”' : '';
      studyEl('study-quote').hidden = !result.quote; studySetStage('reflect');
    }
    if (action !== 'respond' && studyEl('study-rewards').checked) { practice = studyState.award(practice, 'help'); studySave(); studyRenderProgress(); }
    studySay(action === 'hint' ? 'Use the hint, uncover the passage or listen. Take your time.' : 'Notice one thing about your practice, then finish when you choose. This is practice guidance, not a grade.');
  } catch (error) { studySay(error.message); } finally { studySetBusy(false); }
}
studyEl('study-response').onsubmit = event => { event.preventDefault(); if (!studyEl('study-attempt').value.trim()) return studySay('Try a few words, or choose Show me for support.'); studyAct('respond'); };
studyEl('study-hint').onclick = () => studyAct('hint'); studyEl('study-reveal').onclick = () => studyAct('reveal');
studyEl('study-listen').onclick = () => { if (quest) speak(quest.question, studyEl('study-question')); };
studyEl('study-finish').onclick = async () => {
  if (!quest || stage !== 'reflect' || studyBusy) return;
  // Refresh eligibility before recording a source-specific completion or review reference.
  studySetBusy(true);
  try {
    const response = await fetch('/api/session'); if (!response.ok) throw new Error('Refresh the reading library before finishing.');
    const latest = await response.json();
    if (latest.instance_id !== session.instance_id || latest.age_band !== session.age_band || latest.study_source_versions[quest.lesson_id] !== quest.source_fingerprint) throw new Error('The learning space or passage changed. Refresh the reading library; earlier participation is unchanged.');
    session.study_source_versions = latest.study_source_versions;
    practice = studyState.sanitize(practice, session.study_source_versions);
    if (studyEl('study-rewards').checked && studyEl('study-reflect').value === 'help') practice = studyState.award(practice, 'help');
    practice = studyState.finish(practice, quest.lesson_id, quest.source_fingerprint, Number(studyEl('study-review-days').value), studyEl('study-rewards').checked);
    studySave(); studyRenderProgress(); studyReset('You explored one idea. Choose another activity or take a break.');
    if (studyEl('study-rewards').checked && studyEl('study-celebration').value !== 'quiet') { studyEl('study-celebrate').textContent = 'One idea explored. Asking for help and taking your time both count.'; studyEl('study-celebrate').hidden = false; }
  } catch (error) { studySay(error.message); } finally { studySetBusy(false); }
};
studyEl('study-rewards').onchange = () => { studyEl('study-celebrate').hidden = true; studySavePreferences(); studyRenderProgress(); };
studyEl('study-celebration').onchange = () => { studySavePreferences(); studyRenderProgress(); };
studyEl('study-save').onchange = () => { if (studySave()) studySay(studyEl('study-save').checked ? 'Participation totals and review references will stay in this browser. No answers are saved.' : 'Saved practice data removed from this browser. Current practice stays in memory for this visit.'); };
studyEl('study-clear').onclick = () => { practice = studyState.empty(); const saved = studySave(); studyRenderProgress(); if (saved) studySay('Participation totals, achievements and review references cleared for this space.'); };
window.addEventListener('piet-session-loaded', studyLoaded);
window.addEventListener('piet-passage-changed', () => studyReset('Choose how you would like to practise this passage.'));
window.addEventListener('piet-another-explanation', () => { if (studyEl('study-rewards').checked) { practice = studyState.award(practice, 'another'); studySave(); studyRenderProgress(); } });
if (typeof session !== 'undefined' && session) studyLoaded();
