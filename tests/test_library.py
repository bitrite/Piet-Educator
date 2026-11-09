import base64
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from library import Library, split_text
from extract_material import extract, xml
from educator import Educator
from test_educator import CATALOG, FakeModel


def upload(raw=b'There are eight counters. Three counters are blue.', filename='counters.txt'):
    return {'filename': filename, 'content': base64.b64encode(raw).decode(), 'metadata': {
        'title': 'Counters — original test', 'provider': 'Piet demonstration', 'framework': 'Demonstration',
        'grade': 'Foundational numeracy', 'subject': 'Mathematics', 'language': 'English', 'edition': 'Test edition', 'permission': True}}


def zipped(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as book:
        for name, data in files.items():
            book.writestr(name, data)
    return output.getvalue()


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.library = Library(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def review(self, book, status='approved', bands=None, **changes):
        passage = book['passages'][0]
        request = {'text': passage['text'], 'age_bands': ['6-9'] if bands is None else bands,
                   'reviewed_by': 'Test reviewer', 'status': status, 'revision': passage['revision'], 'confirmed': True}
        request.update(changes)
        return self.library.review(passage['id'], request)

    def test_import_is_draft_and_original_survives_restart(self):
        request = upload()
        book = self.library.import_file(request)
        self.assertEqual(book['passages'][0]['status'], 'draft')
        self.assertEqual(self.library.lessons('6-9'), [])
        restarted = Library(self.directory.name)
        self.assertEqual(restarted.original(book['id']), base64.b64decode(request['content']))
        self.assertEqual(len(restarted.list()), 1)

    def test_only_approved_age_eligible_passages_are_available(self):
        book = self.library.import_file(upload())
        self.review(book, bands=['adult'])
        self.assertEqual(self.library.lessons('6-9'), [])
        self.assertEqual(len(self.library.lessons('adult')), 1)
        self.assertIn('Text section 1', self.library.lessons('adult')[0]['source'])
        self.assertEqual(self.library.lessons('adult')[0]['metadata']['grade'], 'Foundational numeracy')

    def test_corrections_preserve_original_and_audit(self):
        book = self.library.import_file(upload())
        updated = self.review(book, text='There are eight counters. Three are blue.')
        p = updated['passages'][0]
        self.assertNotEqual(p['original_text'], p['text'])
        self.assertEqual(p['revision'], 2)
        with self.library.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0], 1)

    def test_revocation_prevents_stale_learner_question(self):
        book = self.library.import_file(upload())
        book = self.review(book)
        model = FakeModel()
        service = Educator(CATALOG, model=model)
        service.library = self.library
        lesson_id = self.library.lessons('6-9')[0]['id']
        self.review(book, status='draft')
        with self.assertRaises(ValueError):
            service.explain({'lesson_id': lesson_id, 'question': 'Explain this.'})
        self.assertEqual(model.calls, [])

    def test_imported_passage_is_used_as_answer_evidence(self):
        book = self.review(self.library.import_file(upload()))
        candidate = {'answer': 'Three counters are blue.', 'quote': 'Three counters are blue.', 'supported': True}
        model = FakeModel(answer=candidate)
        service = Educator(CATALOG, model=model); service.library = self.library
        lesson = self.library.lessons('6-9')[0]
        result = service.explain({'lesson_id': lesson['id'], 'question': 'How many counters are blue?'})
        self.assertEqual(result['status'], 'checked')
        self.assertEqual(model.calls[0]['passage'], book['passages'][0]['text'])
        self.assertEqual(result['source'], lesson['source'])

    def test_withdrawal_during_inference_withholds_answer(self):
        book = self.review(self.library.import_file(upload()))
        candidate = {'answer': 'Three counters are blue.', 'quote': 'Three counters are blue.', 'supported': True}
        parent = self
        class RevokingModel(FakeModel):
            def complete(self, system, content, schema):
                if 'candidate' in content:
                    parent.review(book, status='draft')
                return super().complete(system, content, schema)
        service = Educator(CATALOG, model=RevokingModel(answer=candidate)); service.library = self.library
        lesson = self.library.lessons('6-9')[0]
        self.assertEqual(service.explain({'lesson_id': lesson['id'], 'question': 'Explain this.'})['status'], 'withheld')

    def test_concurrent_review_conflict_and_empty_age_approval_rejected(self):
        book = self.library.import_file(upload())
        with self.assertRaises(ValueError): self.review(book, bands=[])
        with self.assertRaises(ValueError): self.review(book, confirmed=False)
        self.review(book)
        with self.assertRaisesRegex(ValueError, 'changed'): self.review(book)

    def test_permission_file_type_encoding_and_duplicate_checks(self):
        request = upload()
        request['metadata']['permission'] = False
        with self.assertRaises(ValueError): self.library.import_file(request)
        for request in (upload(filename='program.exe'), dict(upload(), content='not base64!'), upload(b'\xff\xfe\x80')):
            with self.assertRaises(ValueError): self.library.import_file(request)
        self.library.import_file(upload())
        with self.assertRaisesRegex(ValueError, 'already'): self.library.import_file(upload())

    def test_filename_cannot_choose_storage_location(self):
        book = self.library.import_file(upload(filename='../../outside.txt'))
        self.assertEqual(book['filename'], 'outside.txt')
        self.assertEqual(len(list((Path(self.directory.name) / 'originals').glob('*.txt'))), 1)

    def test_manual_transcription_starts_as_draft(self):
        book = self.library.import_file(upload())
        result = self.library.add_passage(book['id'], {'location': 'Printed page 8', 'text': 'A transcribed passage.'})
        passage = result['passages'][-1]
        self.assertEqual(passage['original_text'], '')
        self.assertEqual(passage['status'], 'draft')
        self.assertEqual(self.library.lessons('6-9'), [])

    def test_long_passages_are_bounded_without_losing_words(self):
        text = 'A short sentence. ' * 1000
        pieces = list(split_text(text))
        self.assertTrue(all(len(x) <= 2400 for x in pieces))
        self.assertEqual(' '.join(' '.join(pieces).split()), ' '.join(text.split()))

    def test_pdf_text_has_page_locations_and_blank_page_warns(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer = PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject(); stream.set_data(b'BT /F1 12 Tf 20 240 Td (Three counters are blue.) Tj ET')
        page[NameObject('/Contents')] = writer._add_object(stream)
        writer.add_blank_page(width=300, height=300)
        raw = io.BytesIO(); writer.write(raw)
        book = self.library.import_file(upload(raw.getvalue(), 'source.pdf'))
        self.assertIn('PDF page 1', book['passages'][0]['location'])
        self.assertIn('Three counters are blue.', book['passages'][0]['text'])
        self.assertTrue(any('PDF page 2' in x for x in book['warnings']))

    def test_encrypted_pdf_rejected(self):
        from pypdf import PdfWriter
        writer = PdfWriter(); writer.add_blank_page(width=100, height=100); writer.encrypt('test-only')
        raw = io.BytesIO(); writer.write(raw)
        with self.assertRaisesRegex(ValueError, 'Password-protected'):
            self.library.import_file(upload(raw.getvalue(), 'protected.pdf'))

    def test_epub_uses_spine_order_and_ignores_scripts(self):
        raw = zipped({'META-INF/container.xml': '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/book.opf"/></rootfiles></container>',
            'OEBPS/book.opf': '<package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="b" href="second.xhtml" media-type="application/xhtml+xml"/><item id="a" href="first.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="a"/><itemref idref="b"/></spine></package>',
            'OEBPS/first.xhtml': '<html><body><p>First chapter.</p><script>do not import this</script></body></html>',
            'OEBPS/second.xhtml': '<html><body><p>Second chapter.</p></body></html>'})
        book = self.library.import_file(upload(raw, 'reading.epub'))
        self.assertEqual(book['passages'][0]['text'], 'First chapter.')
        self.assertIn('first.xhtml', book['passages'][0]['location'])
        self.assertEqual(book['passages'][1]['text'], 'Second chapter.')

    def test_docx_extracts_text_without_running_document(self):
        raw = zipped({'word/document.xml': '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>A worksheet.</w:t></w:r></w:p></w:body></w:document>'})
        book = self.library.import_file(upload(raw, 'worksheet.docx'))
        self.assertEqual(book['passages'][0]['text'], 'A worksheet.')
        self.assertTrue(any('pagination' in x for x in book['warnings']))

    def test_xml_entity_declarations_rejected(self):
        with self.assertRaises(ValueError): xml(b'<!DOCTYPE a [<!ENTITY x "test">]><a>&x;</a>')


if __name__ == '__main__':
    unittest.main()
