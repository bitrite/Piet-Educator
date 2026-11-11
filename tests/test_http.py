"""HTTP integration with fake model; no Ollama inference required."""
import http.client
import json
from pathlib import Path
import sys
import threading
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import make_server
from educator import Educator
from test_educator import CATALOG, FakeModel


class HttpBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.service = Educator(CATALOG, model=FakeModel())
        cls.server = make_server(port=0, service=cls.service, data_dir=cls.directory.name, owner_key='test-owner-access-code')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.request(method, path, body, headers or {})
        response = conn.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        conn.close()
        return result

    def test_no_cross_origin_or_rebinding_access(self):
        for headers in ({"Origin": "https://other.example"}, {"Host": "attacker.example"}):
            self.assertEqual(self.call("GET", "/api/session", headers=headers)[0], 403)

    def test_post_requires_session_token(self):
        self.assertEqual(self.call("POST", "/api/explain", "{}", {"Content-Type": "application/json"})[0], 403)

    def test_valid_explanation_and_age_tampering(self):
        _, raw, _ = self.call("GET", "/api/session")
        token = json.loads(raw)["token"]
        headers = {"Content-Type": "application/json", "X-Piet-Token": token}
        request = {"lesson_id": "journey", "question": "Explain this"}
        status, raw, _ = self.call("POST", "/api/explain", json.dumps(request), headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["status"], "checked")
        request["age_band"] = "adult"
        self.assertEqual(self.call("POST", "/api/explain", json.dumps(request), headers)[0], 400)

    def test_static_security_headers_and_no_path_traversal(self):
        status, raw, headers = self.call("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Make it make sense", raw)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(self.call("GET", "/../lessons.json")[0], 404)

    def test_learner_token_cannot_access_owner_library(self):
        _, raw, _ = self.call("GET", "/api/session")
        session = json.loads(raw)
        self.assertNotIn("owner_key", session)
        self.assertEqual(self.call("GET", "/api/library", headers={"X-Piet-Token": session["token"]})[0], 403)
        self.assertEqual(self.call("POST", "/api/library/import", '{}', {"Content-Type": "application/json", "X-Piet-Token": session["token"]})[0], 403)
        self.assertEqual(self.call("GET", "/api/library", headers={"X-Piet-Owner": self.server.owner_key})[0], 200)

    def test_drafts_and_age_restrictions_across_http(self):
        from test_library import upload
        book = self.server.library.import_file(upload(b"Only a reviewed passage is visible."))
        _, raw, _ = self.call("GET", "/api/session")
        self.assertNotIn(book["id"], raw.decode())
        passage = book['passages'][0]
        headers = {"Content-Type": "application/json", "X-Piet-Owner": self.server.owner_key}
        review = {"text": passage['text'], "age_bands": ['adult'], "reviewed_by": 'Test reviewer', "status": 'approved', "revision": passage['revision'], "confirmed": True}
        self.assertEqual(self.call("POST", '/api/library/passages/' + passage['id'] + '/review', json.dumps(review), headers)[0], 200)
        _, raw, _ = self.call("GET", "/api/session")
        self.assertNotIn(passage['text'], raw.decode())
        review['age_bands'] = ['6-9']; review['revision'] = 2
        self.assertEqual(self.call("POST", '/api/library/passages/' + passage['id'] + '/review', json.dumps(review), headers)[0], 200)
        _, raw, _ = self.call("GET", "/api/session")
        self.assertIn(passage['text'], raw.decode())

    def test_original_and_draft_details_need_owner_access(self):
        from test_library import upload
        book = self.server.library.import_file(upload(b"Private draft source, different file."))
        for path in ('/api/library/' + book['id'], '/api/library/' + book['id'] + '/original'):
            self.assertEqual(self.call('GET', path)[0], 403)

    def test_study_routes_require_learner_token(self):
        for path in ('/api/study/create', '/api/study/action'):
            self.assertEqual(self.call('POST', path, '{}', {'Content-Type': 'application/json'})[0], 403)

    def test_study_card_and_explicit_support_through_http(self):
        from test_study import StudyModel, CARD
        previous = self.service.model, self.service.judge
        self.service.model = self.service.judge = StudyModel()
        try:
            _, raw, _ = self.call('GET', '/api/session')
            session = json.loads(raw)
            self.assertIn('sharing', session['study_source_versions'])
            headers = {'Content-Type': 'application/json', 'X-Piet-Token': session['token']}
            status, raw, _ = self.call('POST', '/api/study/create', json.dumps({'lesson_id':'sharing','method':'recall','challenge':'familiar'}), headers)
            self.assertEqual(status, 200)
            card = json.loads(raw); self.assertEqual(card['status'], 'checked')
            self.assertNotIn('expected_answer', card)
            status, raw, _ = self.call('POST', '/api/study/action', json.dumps({'activity_id':card['activity_id'],'action':'reveal'}), headers)
            self.assertEqual(status, 200); self.assertEqual(json.loads(raw)['answer'], CARD['expected_answer'])
            status, _, _ = self.call('POST', '/api/study/create', json.dumps({'lesson_id':'sharing','method':'recall','challenge':'familiar','age_band':'adult'}), headers)
            self.assertEqual(status, 400)
        finally:
            self.service.model, self.service.judge = previous


if __name__ == "__main__":
    unittest.main()
