import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_site import PublicationError, SiteError, verify_publication, verify_site


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteVerifierTests(unittest.TestCase):
    def copy_site(self, temp_dir: str) -> Path:
        target = Path(temp_dir) / "site"
        target.mkdir()
        for source in SITE.iterdir():
            (target / source.name).write_bytes(source.read_bytes())
        return target

    def test_repository_site_passes_local_verification(self):
        verify_site(SITE)

    def test_script_element_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            (site / "index.html").write_text("<html><script></script></html>", encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "script"):
                verify_site(site)

    def test_external_asset_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            (site / "index.html").write_text(html.replace("styles.css", "https://example.com/a.css"), encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "external"):
                verify_site(site)

    def test_form_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            (site / "index.html").write_text(html + "<form></form>", encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "form"):
                verify_site(site)

    def test_subject_data_language_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            prohibited = "subject" + " identifier"
            (site / "index.html").write_text(html + prohibited, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "prohibited public content"):
                verify_site(site)

    def test_unicode_control_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            (site / "index.html").write_text(html + "\u202e", encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "Unicode control"):
                verify_site(site)

    def test_internal_lifecycle_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            (site / "index.html").write_text(html + "<!-- " + "E" + "PIC-123-45 -->", encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "internal metadata"):
                verify_site(site)

    def test_oversize_file_is_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            (site / "index.html").write_bytes(b"x" * 300_001)
            with self.assertRaisesRegex(SiteError, "size limit"):
                verify_site(site)

    def test_publication_fails_closed_for_missing_decisions(self):
        with self.assertRaises(PublicationError) as context:
            verify_publication(ROOT / "publication.json")
        self.assertEqual(
            context.exception.errors,
            ["publication provider is missing"],
        )

    def test_publication_rejects_placeholder_decisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "publication.json"
            config.write_text(json.dumps({"provider": "TBD", "correction_endpoint": "https://example.com"}), encoding="utf-8")
            with self.assertRaises(PublicationError) as context:
                verify_publication(config)
            self.assertIn("publication provider must be a final non-placeholder value", context.exception.errors)
            self.assertIn("correction endpoint must use the canonical host or its subdomain", context.exception.errors)


if __name__ == "__main__":
    unittest.main()
