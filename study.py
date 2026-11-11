"""Source-gated study activities. Cache teaching cards, never learner responses."""
import hashlib
import json
import secrets
import threading
import time
from collections import OrderedDict
from educator import AGE_BANDS, ModelUnavailable, SYSTEM

METHODS = {
    "recall": "Help me remember: ask one concrete retrieval question, with a short hint and source-supported answer.",
    "review": "Bring it back: revisit one idea with a retrieval question, without assuming what the learner previously knew.",
    "teach": "Let me teach you: invite the learner to explain one idea in their own words. The expected answer gives key meaning, not an exact wording requirement.",
    "worked": "Show me, then help me try: give a short worked example, then one closely related practice question. Keep any illustrative example clearly labelled and correct. Do not invent source facts.",
    "concrete": "Make it concrete: describe familiar objects or a simple scene, connect them explicitly to the passage's idea, then ask one question. This is a verbal picture, not a generated image.",
    "mission": "One small mission: one manageable task to find or explain a key idea, followed by one short content question. Reflection is offered separately by the interface. No timer, compulsory break schedule or pressure to continue.",
}
FIELDS = ("instruction", "worked_example", "question", "hint", "expected_answer", "quote")
CARD_SCHEMA = {"type": "object", "properties": {
    **{name: {"type": "string"} for name in FIELDS}, "supported": {"type": "boolean"}},
    "required": list(FIELDS) + ["supported"], "additionalProperties": False}


def fingerprint(lesson):
    evidence = {key: lesson.get(key) for key in ("id", "text", "source", "age_bands", "reviewed_by", "reviewed_on")}
    return hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Study:
    def __init__(self, educator, now=None, capacity=128, ttl=3600):
        self.educator = educator
        self.now = now or time.monotonic
        self.capacity, self.ttl = capacity, ttl
        self.cards = OrderedDict()
        self.lock = threading.Lock()

    def lesson(self, lesson_id):
        lesson = next((x for x in self.educator.available_lessons() if x["id"] == lesson_id), None)
        if not lesson:
            raise ValueError("This passage is no longer available for this age. Refresh the reading library.")
        return lesson

    def create(self, request):
        if not isinstance(request, dict) or set(request) != {"lesson_id", "method", "challenge"}:
            raise ValueError("Choose a passage and study method.")
        method, challenge = request["method"], request["challenge"]
        if not isinstance(method, str) or method not in METHODS or challenge not in ("familiar", "explore"):
            raise ValueError("Choose a study method and a comfortable challenge.")
        lesson = self.lesson(request["lesson_id"])
        instruction = METHODS[method]
        try:
            candidate = self.educator.model.complete(SYSTEM + "\nCreate one short study card using the requested fields. "
                "Keep the TOTAL words across instruction, worked_example, question, hint and expected_answer "
                "within the given word limit. Use plain text. Keep worked_example empty except for worked/concrete "
                "methods. Give a nonempty question, hint and expected_answer. The question must have a "
                "source-supported answer. A hint should help without simply giving the full answer. "
                "Never give points, speed targets, diagnoses, public comparisons or rewards for avoiding help.",
                {"age_band": self.educator.band, "style": AGE_BANDS[self.educator.band][2],
                 "word_limit": AGE_BANDS[self.educator.band][1], "passage": lesson["text"],
                 "method": instruction, "challenge": "Direct practice of a familiar idea." if challenge == "familiar" else "A gentle explanatory connection; same age policy and no extra reward."}, CARD_SCHEMA)
            if not isinstance(candidate, dict) or set(candidate) != set(FIELDS) | {"supported"}:
                return self.educator.withheld()
            if any(not isinstance(candidate[k], str) or len(candidate[k]) > 1500 for k in FIELDS):
                return self.educator.withheld()
            if any(not candidate[k].strip() for k in ("instruction", "question", "hint", "expected_answer", "quote")):
                return self.educator.withheld()
            if method in ("worked", "concrete") and not candidate["worked_example"].strip():
                return self.educator.withheld()
            # Method-specific scaffolding must not depend on the model following a label.
            if method not in ('worked', 'concrete'):
                candidate['worked_example'] = ''
            if method == 'teach':
                candidate['instruction'] = 'Teach this idea back in your own words. Different wording is welcome.'
                candidate['question'] = 'Explain your reasoning in your own words: ' + candidate['question']
            elif method == 'mission':
                candidate['instruction'] = 'Your small mission: explore one idea in this passage, try the question, then reflect. Read, listen or ask for help.'
            elif method == 'review':
                candidate['instruction'] = 'Revisit this idea at your own pace. See what you remember; support is always available.'
            elif method == 'worked':
                candidate['worked_example'] = 'Worked example: ' + candidate['worked_example']
                candidate['question'] = 'Practice example: ' + candidate['question']
                candidate['hint'] = 'Use the worked example’s method with the numbers in your practice question. You can ask for the suggested answer.'
            elif method == 'concrete':
                candidate['worked_example'] = 'Picture this scene: ' + candidate['worked_example']
            combined = "\n".join(candidate[k] for k in FIELDS if k != "quote")
            result = self.educator.checked_result({"answer": combined, "quote": candidate["quote"],
                "supported": candidate["supported"]}, lesson, "Create a study activity: " + instruction, requirements=instruction)
            if result["status"] != "checked":
                return result
            activity_id = secrets.token_urlsafe(24)
            entry = {"lesson_id": lesson["id"], "fingerprint": fingerprint(lesson), "created": self.now(), "card": candidate}
            with self.lock:
                self.cards[activity_id] = entry
                while len(self.cards) > self.capacity:
                    self.cards.popitem(last=False)
            # No expected answer or source quote is sent before the learner asks for support.
            return {"status": "checked", "activity_id": activity_id, "method": method,
                "source_fingerprint": entry["fingerprint"], "instruction": candidate["instruction"],
                "worked_example": candidate["worked_example"], "question": candidate["question"],
                "validation": result["validation"]}
        except ModelUnavailable:
            return {"status": "unavailable", "answer": "The local study service is unavailable. You can still read or listen to the passage."}

    def act(self, request):
        if not isinstance(request, dict) or set(request) - {"activity_id", "action", "attempt"}:
            raise ValueError("Choose a study activity and action.")
        action, activity_id = request.get("action"), request.get("activity_id")
        if action not in ("hint", "reveal", "respond") or not isinstance(activity_id, str):
            raise ValueError("Choose a valid study action.")
        if action != "respond" and "attempt" in request:
            raise ValueError("A practice response is only used for feedback.")
        with self.lock:
            entry = self.cards.get(activity_id)
        if not entry or self.now() - entry["created"] >= self.ttl:
            raise ValueError("This activity has expired. Start a fresh quest; no progress is lost.")
        lesson = self.lesson(entry["lesson_id"])
        if fingerprint(lesson) != entry["fingerprint"]:
            raise ValueError("This passage changed after review. Refresh the reading library and start again.")
        card = entry["card"]
        if action == "hint":
            return {"status": "checked", "answer": card["hint"]}
        if action == "reveal":
            return {"status": "checked", "answer": card["expected_answer"], "quote": card["expected_answer"], 'quote_kind':'practice',
                    "source": lesson["source"] + ' · checked practice reference', "validation": "Checked practice guidance, not a grade or proof of understanding."}
        attempt = request.get("attempt")
        if not isinstance(attempt, str) or not 1 <= len(attempt.strip()) <= 800:
            raise ValueError("Write a short practice response of up to 800 characters, or choose Show me.")
        result = self.educator.explain({"lesson_id": lesson["id"], "mode": "practice_feedback",
            "question": "Offer gentle feedback on this practice response, without a score or judgement of ability:\n" + attempt,
            "previous": ""}, practice={'question':card['question'], 'reference_answer':card['expected_answer']})
        if fingerprint(self.lesson(entry["lesson_id"])) != entry["fingerprint"]:
            return self.educator.withheld()
        return result
