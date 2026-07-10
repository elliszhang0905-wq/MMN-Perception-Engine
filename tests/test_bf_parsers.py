import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from bf_factory.parsers import BFParseError, parse_document, validate_upload
from bf_factory.storage import sanitize_filename, store_document


def zip_bytes(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return output.getvalue()


class BFParserTest(unittest.TestCase):
    def test_filename_is_sanitized_and_stored_inside_project_scope(self):
        self.assertEqual(sanitize_filename("../../客户<>brief.docx"), "客户_brief.docx")
        with tempfile.TemporaryDirectory() as tmp:
            stored = store_document(
                root=tmp,
                org_id="org/../../1",
                client_key="client-a",
                project_id="project-a",
                document_id="doc-a",
                filename="../../客户<>brief.docx",
                data=b"PK\x03\x04test",
            )
            self.assertTrue(stored.exists())
            self.assertTrue(str(stored.resolve()).startswith(str(Path(tmp).resolve())))
            self.assertEqual(stored.name, "客户_brief.docx")

    def test_upload_validation_rejects_executable_renamed_as_image(self):
        with self.assertRaises(BFParseError):
            validate_upload("attack.png", b"MZ" + b"\x00" * 30)

    def test_docx_parser_preserves_paragraph_and_table_locators(self):
        docx = zip_bytes(
            {
                "[Content_Types].xml": "<Types/>",
                "word/document.xml": """
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                  <w:body>
                    <w:p><w:r><w:t>智己L6探店项目</w:t></w:r></w:p>
                    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>必须表达</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>底盘</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
                  </w:body>
                </w:document>
                """,
            }
        )
        result = parse_document("brief.docx", docx)
        self.assertEqual(result["format"], "DOCX")
        self.assertEqual(result["segments"][0]["paragraphNo"], 1)
        self.assertEqual(result["segments"][0]["text"], "智己L6探店项目")
        self.assertEqual(result["segments"][1]["blockType"], "TABLE")
        self.assertEqual(result["segments"][1]["table"][0], ["必须表达", "底盘"])

    def test_pptx_parser_preserves_slide_number_and_notes(self):
        pptx = zip_bytes(
            {
                "[Content_Types].xml": "<Types/>",
                "ppt/slides/slide1.xml": """
                <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>高质感摄影</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
                </p:sld>
                """,
                "ppt/notesSlides/notesSlide1.xml": """
                <p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                  <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>车身必须清洁</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>
                </p:notes>
                """,
            }
        )
        result = parse_document("brief.pptx", pptx)
        self.assertEqual(result["segments"][0]["slideNo"], 1)
        self.assertEqual(result["segments"][0]["text"], "高质感摄影")
        self.assertEqual(result["segments"][1]["blockType"], "NOTES")
        self.assertEqual(result["segments"][1]["text"], "车身必须清洁")

    def test_pdf_image_csv_and_markdown_have_traceable_segments(self):
        pdf = b"%PDF-1.4\n1 0 obj <<>> stream\nBT (Cloud review argument) Tj ET\nendstream\nendobj\n%%EOF"
        pdf_result = parse_document("brief.pdf", pdf)
        self.assertEqual(pdf_result["segments"][0]["pageNo"], 1)
        self.assertIn("Cloud review argument", pdf_result["segments"][0]["text"])

        image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        image_result = parse_document("brief.png", image)
        self.assertEqual(image_result["segments"][0]["blockType"], "IMAGE")
        self.assertTrue(image_result["segments"][0]["locator"]["ocrRequired"])

        csv_result = parse_document("brief.csv", "字段,内容\n车型,智己L6\n".encode("utf-8"))
        self.assertEqual(csv_result["segments"][0]["sheetName"], "CSV")
        self.assertEqual(csv_result["segments"][0]["table"][0], ["字段", "内容"])

        md_result = parse_document("brief.md", "# 项目背景\n探店传播".encode("utf-8"))
        self.assertEqual(md_result["segments"][1]["paragraphNo"], 2)


if __name__ == "__main__":
    unittest.main()
