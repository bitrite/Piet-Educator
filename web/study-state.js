/* Participation and voluntary review references only: never store learner answers. */
(function (root) {
  const DAY = 86400000;
  const BADGES = ['tried', 'help', 'reflected', 'another'];
  function empty() { return {version: 1, completed: 0, badges: [], reviews: []}; }
  function sanitize(value, versions, now = Date.now()) {
    if (!value || value.version !== 1) return empty();
    const completed = Number.isSafeInteger(value.completed) && value.completed >= 0 ? Math.min(100000, value.completed) : 0;
    const badges = Array.isArray(value.badges) ? [...new Set(value.badges.filter(x => BADGES.includes(x)))] : [];
    const seen = new Set();
    const reviews = (Array.isArray(value.reviews) ? value.reviews : []).filter(x => {
      if (!x || typeof x.lesson_id !== 'string' || seen.has(x.lesson_id) || !versions[x.lesson_id] || versions[x.lesson_id] !== x.version || !Number.isFinite(x.due) || Math.abs(x.due - now) > 365 * DAY) return false;
      seen.add(x.lesson_id); return true;
    }).slice(0, 50).map(x => ({lesson_id: x.lesson_id, version: x.version, due: x.due}));
    return {version: 1, completed, badges, reviews};
  }
  function award(state, badge) {
    return {...state, badges: BADGES.includes(badge) ? [...new Set([...state.badges, badge])] : state.badges};
  }
  function finish(state, lessonId, version, days, reward = true, now = Date.now()) {
    if (![0, 1, 3, 7].includes(days)) throw new Error('Choose a review interval.');
    const reviews = state.reviews.filter(x => x.lesson_id !== lessonId);
    if (days) reviews.push({lesson_id: lessonId, version, due: now + days * DAY});
    let next = {...state, reviews: reviews.slice(-50)};
    if (reward) next = award(award({...next, completed: Math.min(100000, next.completed + 1)}, 'tried'), 'reflected');
    return next;
  }
  const api = {empty, sanitize, award, finish};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.PietStudyState = api;
})(typeof window !== 'undefined' ? window : globalThis);
