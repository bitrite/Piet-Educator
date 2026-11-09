const $ = id => document.getElementById(id);
let session, activeLesson, previous = '', answer = '', speaking = null;
const prefIds = ['size', 'spacing', 'font', 'theme', 'speed'];
function preferences() {
  document.documentElement.style.setProperty('--read-size', `${$('size').value}px`);
  document.documentElement.style.setProperty('--line', $('spacing').value);
  document.documentElement.style.setProperty('--read-font', $('font').value);
  document.body.dataset.theme = $('theme').value;
  try { localStorage.setItem('piet-reading-v1', JSON.stringify(Object.fromEntries(prefIds.map(id => [id, $(id).value])))); } catch (_) {}
}
try {
  const saved = JSON.parse(localStorage.getItem('piet-reading-v1') || '{}');
  for (const id of prefIds) if (saved[id] !== undefined) $(id).value = saved[id];
} catch (_) {}
for (const id of prefIds) $(id).addEventListener('input', preferences);
preferences();
function stopReading() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  speaking = null;
  document.querySelectorAll('.spoken').forEach(e => e.classList.remove('spoken'));
}
function localVoice() {
  return window.speechSynthesis?.getVoices().find(v => v.localService && /^en(?:-|$)/i.test(v.lang));
}
function voiceStatus() {
  $('voice-status').textContent = localVoice() ? 'An English voice installed on this device is available. Highlighting depends on your voice.' : 'No local English voice is available yet. Install an offline system voice to listen.';
  $('listen').disabled = !localVoice();
  $('listen-answer').disabled = !localVoice();
}
function speak(text, container) {
  stopReading();
  const voice = localVoice();
  if (!voice || !text) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = voice; utterance.lang = voice.lang; utterance.rate = Number($('speed').value);
  // Keep original text unchanged; word spans follow actual speech boundary events.
  container.replaceChildren();
  const spans = []; const pattern = /\S+|\s+/g; let match;
  while ((match = pattern.exec(text)) !== null) {
    const span = document.createElement('span'); span.textContent = match[0];
    spans.push({start: match.index, end: match.index + match[0].length, span}); container.append(span);
  }
  utterance.onboundary = event => {
    if (speaking !== utterance) return;
    for (const part of spans) part.span.classList.toggle('spoken', event.charIndex >= part.start && event.charIndex < part.end);
  };
  utterance.onend = stopReading;
  utterance.onerror = () => { stopReading(); $('voice-status').textContent = 'This voice could not finish. You can keep reading the text.'; };
  speaking = utterance; window.speechSynthesis.speak(utterance);
}
$('stop').onclick = stopReading;
$('listen').onclick = () => speak(activeLesson.text, $('passage'));
$('listen-answer').onclick = () => speak(answer, $('answer'));
if ('speechSynthesis' in window) window.speechSynthesis.addEventListener('voiceschanged', voiceStatus);
voiceStatus();
function chooseLesson() {
  stopReading(); activeLesson = session.lessons.find(x => x.id === $('lesson').value);
  $('title').textContent = activeLesson.title; $('passage').textContent = activeLesson.text;
  $('source').textContent = activeLesson.source; previous = ''; answer = '';
  $('answer').textContent = ''; $('question').value = ''; $('quote').hidden = true;
  $('validation').textContent = ''; $('feedback').hidden = true; $('status').textContent = 'Ready when you are.';
}
$('lesson').onchange = chooseLesson;
function fillPassages() {
  const before = $('lesson').value;
  $('lesson').replaceChildren();
  for (const lesson of session.lessons.filter(x => (x.material_id || 'samples') === $('material').value)) {
    const option = document.createElement('option'); option.value = lesson.id; option.textContent = lesson.title; $('lesson').append(option);
  }
  if ([...$('lesson').options].some(x => x.value === before)) $('lesson').value = before;
  chooseLesson();
}
$('material').onchange = fillPassages;
$('ask').onsubmit = async event => {
  event.preventDefault(); stopReading();
  $('explain').disabled = true; $('again').disabled = true; $('lesson').disabled = true; $('material').disabled = true; $('refresh-reading').disabled = true;
  $('feedback').hidden = true; $('quote').hidden = true; $('answer').textContent = ''; $('validation').textContent = '';
  $('status').textContent = 'Piet is preparing and checking an explanation. This may take a little time.';
  try {
    const response = await fetch('/api/explain', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Piet-Token': session.token}, body: JSON.stringify({lesson_id: activeLesson.id, question: $('question').value.trim() || 'Explain this passage.', mode: $('method').value, previous})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Please try again.');
    answer = result.answer; $('answer').textContent = answer;
    $('status').textContent = result.status === 'checked' ? 'Here is another way to explore it.' : 'Let’s take a moment.';
    $('validation').textContent = result.validation || '';
    if (result.status === 'checked') {
      previous = answer; $('quote').textContent = `From the passage: “${result.quote}”`;
      $('quote').hidden = false; $('feedback').hidden = false;
    }
  } catch (error) { $('status').textContent = error.message; }
  finally { $('explain').disabled = false; $('again').disabled = false; $('lesson').disabled = false; $('material').disabled = false; $('refresh-reading').disabled = false; }
};
$('again').onclick = () => {
  const select = $('method'); select.selectedIndex = (select.selectedIndex + 1) % select.options.length;
  $('ask').requestSubmit();
};
$('understood').onclick = () => { $('status').textContent = 'You can explain it in your own words, explore another passage, or take a break.'; };
async function start() {
  try {
    const response = await fetch('/api/session'); if (!response.ok) throw new Error('Could not open this learning space.');
    session = await response.json(); $('age').textContent = `${session.age_label} • Local learning space`;
    const selected = $('material').value;
    const resources = new Map([['samples', 'Original sample lessons']]);
    for (const lesson of session.lessons) if (lesson.material_id) resources.set(lesson.material_id, lesson.metadata.title + ' · ' + lesson.metadata.grade + ' · ' + lesson.metadata.subject);
    $('material').replaceChildren();
    for (const [id, title] of resources) { const option = document.createElement('option'); option.value = id; option.textContent = title; $('material').append(option); }
    if (resources.has(selected)) $('material').value = selected;
    if (!session.lessons.length) throw new Error('No reviewed passages are available for this age setting.');
    fillPassages();
  } catch (error) { $('status').textContent = error.message; $('explain').disabled = true; }
}
$('refresh-reading').onclick = start;
start();
