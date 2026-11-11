const {test} = require('node:test');
const assert = require('node:assert/strict');
const state = require('../web/study-state.js');
const now = Date.UTC(2026, 10, 11);

test('hints and direct responses earn the same participation completion', () => {
  const without = state.finish(state.empty(), 'sharing', 'v1', 1, true, now);
  const helped = state.finish(state.award(state.empty(), 'help'), 'sharing', 'v1', 1, true, now);
  assert.equal(without.completed, helped.completed);
  assert.ok(helped.badges.includes('help'));
});
test('breaks and elapsed days do not subtract achievements or progress', () => {
  const completed = state.finish(state.empty(), 'sharing', 'v1', 1, true, now);
  const later = state.sanitize(completed, {sharing: 'v1'}, now + 8 * 86400000);
  assert.equal(later.completed, 1);
  assert.deepEqual(later.badges, completed.badges);
  assert.equal(later.reviews.length, 1);
});
test('revoked or revised sources disappear from review references', () => {
  const completed = state.finish(state.empty(), 'sharing', 'v1', 1, true, now);
  assert.equal(state.sanitize(completed, {}, now).reviews.length, 0);
  assert.equal(state.sanitize(completed, {sharing: 'v2'}, now).reviews.length, 0);
});
test('stored records exclude answers, prompts and arbitrary achievement labels', () => {
  const value = {version: 1, completed: 2, answer: 'private', badges: ['tried', 'untrusted'], reviews: [{lesson_id:'sharing',version:'v1',due:now,answer:'private'}]};
  const clean = state.sanitize(value, {sharing:'v1'}, now);
  assert.ok(!JSON.stringify(clean).includes('private'));
  assert.deepEqual(clean.badges, ['tried']);
});
test('gamification can be off while a voluntary review is scheduled', () => {
  const result = state.finish(state.empty(), 'sharing', 'v1', 3, false, now);
  assert.equal(result.completed, 0); assert.deepEqual(result.badges, []);
  assert.equal(result.reviews[0].due, now + 3 * 86400000);
});
test('revisiting can replace or remove a voluntary review, without duplicates', () => {
  const first = state.finish(state.empty(), 'sharing', 'v1', 1, true, now);
  const next = state.finish(first, 'sharing', 'v1', 7, true, now);
  assert.equal(next.reviews.length, 1);
  assert.equal(state.finish(next, 'sharing', 'v1', 0, true, now).reviews.length, 0);
});
test('malformed records do not create scores, deadlines or saved answers', () => {
  assert.deepEqual(state.sanitize(null, {}), state.empty());
  assert.equal(state.sanitize({version:1,completed:-4,badges:'bad',reviews:'bad'},{}).completed, 0);
  assert.throws(() => state.finish(state.empty(), 'sharing', 'v1', 100));
});
