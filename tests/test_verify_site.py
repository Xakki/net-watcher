import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from tools.verify_site import (
    MAX_DECODE_ITERATIONS,
    MAX_FILE_BYTES,
    MAX_TEXT_CODEPOINTS,
    PublicationError,
    SiteError,
    decoded_views,
    load_boundary,
    read_bounded,
    verify_publication,
    verify_publishable_repository,
    verify_repository,
    verify_site,
)


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteVerifierTests(unittest.TestCase):
    def copy_site(self, temp_dir: str) -> Path:
        target = Path(temp_dir) / "site"
        target.mkdir()
        for source in SITE.iterdir():
            (target / source.name).write_bytes(source.read_bytes())
        return target

    def copy_repository(self, root: Path) -> set[str]:
        tracked = set(json.loads((ROOT / "publication-boundary.json").read_text())["tracked_files"])
        for relative in tracked:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        return tracked

    def init_repository(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Verifier Tests"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)

    def test_repository_site_passes_local_verification(self):
        verify_site(SITE)

    def test_note_marker_text_meets_wcag_contrast(self):
        css = (SITE / "styles.css").read_text(encoding="utf-8")
        colors = dict(re.findall(r"--([a-z-]+): (#[0-9a-f]{6});", css))
        marker = re.search(r"\.note-marker \{(?P<rules>[^}]*)\}", css)
        if marker is None:
            self.fail("note marker rules are missing")
        color = re.search(r"color: var\(--(?P<token>[a-z-]+)\);", marker.group("rules"))
        if color is None:
            self.fail("note marker text color is missing")

        def luminance(hex_color: str) -> float:
            channels = [int(hex_color[offset : offset + 2], 16) / 255 for offset in (1, 3, 5)]
            linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        foreground = luminance(colors[color.group("token")])
        background = luminance(colors["paper"])
        contrast = (max(foreground, background) + 0.05) / (min(foreground, background) + 0.05)
        self.assertGreaterEqual(contrast, 4.5)

    def test_mobile_hero_fits_scrollbar_reduced_layout_viewport(self):
        css = (SITE / "styles.css").read_text(encoding="utf-8")
        narrow = re.search(r"@media \(max-width: 320px\) \{(?P<rules>.*?)\n\}", css, re.DOTALL)
        if narrow is None:
            self.fail("narrow layout rules are missing")
        heading = re.search(
            r"h1 \{ font-size: clamp\((?P<minimum>[0-9.]+)rem, (?P<fluid>[0-9.]+)vw, [0-9.]+rem\); \}",
            narrow.group("rules"),
        )
        if heading is None:
            self.fail("narrow hero fluid typography is missing")
        minimum_px = float(heading.group("minimum")) * 16
        fluid_scale = float(heading.group("fluid")) / 100
        longest_line_em = 6.3
        for inner_width, client_width in ((280, 265), (320, 305)):
            with self.subTest(inner_width=inner_width, client_width=client_width):
                font_size = max(minimum_px, fluid_scale * inner_width)
                heading_right = 16 + longest_line_em * font_size
                document_scroll_width = max(client_width, heading_right)
                body_scroll_width = max(client_width, heading_right)
                self.assertLessEqual(heading_right, client_width - 4)
                self.assertLessEqual(document_scroll_width, client_width)
                self.assertLessEqual(body_scroll_width, client_width)

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

    def test_external_srcset_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            html += '<img src="local.png" srcset="local.png 1x, https://example.com/a.png 2x" alt="">'
            (site / "index.html").write_text(html, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "external"):
                verify_site(site)

    def test_encoded_protocol_relative_srcset_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            html += '<source srcset="local.png 1x, &#47;&#47;example.com/a.png 2x">'
            (site / "index.html").write_text(html, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "external"):
                verify_site(site)

    def test_external_base_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            html = html.replace("<head>", '<head><base href="https://example.com/">')
            (site / "index.html").write_text(html, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "external"):
                verify_site(site)

    def test_external_network_request_attributes_are_rejected(self):
        fragments = (
            '<img attributionsrc="https://example.com/register" alt="">',
            '<link imagesrcset="local.png 1x, https://example.com/a.png 2x">',
            '<svg><linearGradient href="https://example.com/gradient.svg"></linearGradient></svg>',
        )
        for fragment in fragments:
            with self.subTest(fragment=fragment), tempfile.TemporaryDirectory() as temp_dir:
                site = self.copy_site(temp_dir)
                html = (site / "index.html").read_text(encoding="utf-8")
                (site / "index.html").write_text(html + fragment, encoding="utf-8")
                with self.assertRaisesRegex(SiteError, "external"):
                    verify_site(site)

    def test_local_asset_attributes_are_accepted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            html += '<img src="local.png" srcset="small.png 1x, large.png 2x" alt="">'
            (site / "index.html").write_text(html, encoding="utf-8")
            verify_site(site)

    def test_unsafe_asset_scheme_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            html = (site / "index.html").read_text(encoding="utf-8")
            html += '<img src="javascript:alert(1)" alt="">'
            (site / "index.html").write_text(html, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "unsafe"):
                verify_site(site)

    def test_external_css_import_forms_are_rejected(self):
        imports = (
            '@import "https://example.com/a.css";',
            "@IMPORT url(//example.com/a.css);",
            "@import url('https\\3a //example.com/a.css');",
        )
        for rule in imports:
            with self.subTest(rule=rule), tempfile.TemporaryDirectory() as temp_dir:
                site = self.copy_site(temp_dir)
                css = (site / "styles.css").read_text(encoding="utf-8")
                (site / "styles.css").write_text(rule + "\n" + css, encoding="utf-8")
                with self.assertRaisesRegex(SiteError, "external CSS"):
                    verify_site(site)

    def test_escaped_external_css_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            css = (site / "styles.css").read_text(encoding="utf-8")
            css += "\n.example { background-image: url(https\\3a //example.com/a.png); }\n"
            (site / "styles.css").write_text(css, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "external CSS"):
                verify_site(site)

    def test_local_css_import_and_import_text_are_accepted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site = self.copy_site(temp_dir)
            css = (site / "styles.css").read_text(encoding="utf-8")
            css = (
                '@import "styles.css";\n'
                '/* @import "https://example.com/a.css"; */\n'
                '.note::before { content: "@import url(https://example.com/a.css)"; }\n'
                + css
            )
            (site / "styles.css").write_text(css, encoding="utf-8")
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
            (site / "index.html").write_text(html + "subject" + " identifier", encoding="utf-8")
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

    def test_bounded_reader_rejects_limit_plus_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "large.txt"
            path.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
            with self.assertRaisesRegex(SiteError, "size limit"):
                read_bounded(path)

    def test_repository_uses_manifest_set_and_ignores_local_files(self):
        ignored = ROOT / ".private" / "must-not-be-read"
        ignored.parent.mkdir(exist_ok=True)
        ignored.write_bytes(b"\xffprivate")
        try:
            verify_repository(ROOT)
        finally:
            ignored.unlink()
            ignored.parent.rmdir()

    def test_parent_directory_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            shutil.copytree(root / "docs", outside_dir + "/docs")
            shutil.rmtree(root / "docs")
            (root / "docs").symlink_to(Path(outside_dir) / "docs", target_is_directory=True)
            with self.assertRaisesRegex(SiteError, "cannot open"):
                verify_repository(root, tracked_files=tracked)

    def test_manifest_unknown_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            path = root / "publication-boundary.json"
            data = json.loads(path.read_text())
            data["unexpected"] = []
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "keys"):
                load_boundary(root)

    def test_manifest_duplicate_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            path = root / "publication-boundary.json"
            text = path.read_text()
            path.write_text(text.replace('"served_files":', '"served_files": [], "served_files":', 1), encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "duplicate"):
                load_boundary(root)

    def test_manifest_duplicate_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            path = root / "publication-boundary.json"
            data = json.loads(path.read_text())
            data["served_files"].append(data["served_files"][0])
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "sorted unique"):
                load_boundary(root)

    def test_manifest_prohibited_classes_must_match_canonical_contract(self):
        canonical = json.loads((ROOT / "publication-boundary.json").read_text())["prohibited_classes"]
        mutations = {
            "replacement": ["bananas"],
            "removal": canonical[:-1],
            "addition": [*canonical, "untrusted extra class"],
            "reorder": [canonical[1], canonical[0], *canonical[2:]],
        }
        for name, prohibited_classes in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                self.copy_repository(root)
                path = root / "publication-boundary.json"
                boundary = json.loads(path.read_text())
                boundary["prohibited_classes"] = prohibited_classes
                path.write_text(json.dumps(boundary), encoding="utf-8")
                with self.assertRaisesRegex(SiteError, "prohibited classes"):
                    load_boundary(root)

    def test_tracked_set_drift_is_rejected_both_directions(self):
        expected = set(json.loads((ROOT / "publication-boundary.json").read_text())["tracked_files"])
        with self.assertRaisesRegex(SiteError, "missing"):
            verify_repository(ROOT, tracked_files=expected - {"README.md"})
        with self.assertRaisesRegex(SiteError, "extra"):
            verify_repository(ROOT, tracked_files=expected | {"extra.txt"})

    def test_gitignore_and_manifest_drift_are_rejected_both_directions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            (root / ".gitignore").write_text((root / ".gitignore").read_text() + "extra-local/\n", encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "ignored-local"):
                verify_repository(root, tracked_files=tracked)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            boundary = json.loads((root / "publication-boundary.json").read_text())
            boundary["ignored_local_patterns"].append("extra-local/")
            boundary["ignored_local_patterns"].sort()
            (root / "publication-boundary.json").write_text(json.dumps(boundary), encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "ignored-local"):
                verify_repository(root, tracked_files=tracked)

    def test_double_url_encoded_path_is_rejected(self):
        private_path = "/" + "home" + "/someone/private"
        self.assertDisclosureRejected(quote(quote(private_path, safe=""), safe=""))

    def test_base64_then_url_encoded_path_is_rejected(self):
        private_path = "/" + "home" + "/someone/private"
        payload = base64.b64encode(quote(private_path, safe="").encode()).decode()
        self.assertDisclosureRejected(payload)

    def test_nested_entity_url_static_encoding_is_rejected(self):
        payload = "\\u0026#x25;252Fhome" + "\\x25" + "252Fsomeone%252Fprivate"
        self.assertDisclosureRejected(payload)

    def test_decode_over_iteration_limit_fails_closed(self):
        payload = "/" + "home" + "/someone/private"
        for _ in range(MAX_DECODE_ITERATIONS + 1):
            payload = quote(payload, safe="")
        with self.assertRaisesRegex(SiteError, "decode iteration"):
            list(decoded_views(payload))

    def test_unicode_normalization_expansion_fails_budget(self):
        payload = "\ufdfa" * ((MAX_TEXT_CODEPOINTS // 10) + 1)
        with self.assertRaisesRegex(SiteError, "decode budget"):
            list(decoded_views(payload))

    def test_registry_account_domain_is_rejected(self):
        self.assertDisclosureRejected("See https://" + "account" + "." + "arin" + ".net")

    def test_registry_account_workflow_is_rejected(self):
        self.assertDisclosureRejected("Create an " + "AR" + "IN Online account")

    def test_registry_request_flow_is_rejected(self):
        self.assertDisclosureRejected("AR" + "IN " + "request" + " form workflow")

    def test_registry_unicode_variant_is_rejected(self):
        phrase = "ＡＲ" + "ＩＮ " + "application" + " submission " + "instructions"
        self.assertDisclosureRejected(quote(phrase, safe=""))

    def test_registry_reviewer_workflow_regressions_are_rejected(self):
        identity = "AR" + "IN Online"
        phrases = (
            f"Signup with {identity} for an account.",
            f"Enroll for an account with {identity}.",
            f"Enroll with {identity} for an account.",
            f"Complete an {identity} signup.",
            f"Create an {identity} identity.",
            f"Open an {identity} profile.",
        )
        for phrase in phrases:
            variants = (
                phrase,
                quote(phrase, safe=""),
                base64.b64encode(phrase.encode()).decode(),
                phrase.replace(identity, "A\u200bR\x00IN Online"),
            )
            for variant in variants:
                with self.subTest(phrase=phrase, variant=variant):
                    self.assertProhibitedRejected(variant)

    def test_registry_onboarding_vocabulary_and_word_order_are_rejected(self):
        identity = "AR" + "IN Online"
        phrases = (
            f"Signup with {identity}.",
            f"Sign-up with {identity}.",
            f"Sign up with {identity}.",
            f"Enroll with {identity}.",
            f"Enrol with {identity}.",
            f"Complete the signup for {identity}.",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertDisclosureRejected(phrase)
        for action in ("Create", "Open", "Register", "Start", "Establish"):
            for noun in ("account", "identity", "profile"):
                phrases = (
                    f"{action} a {noun} with {identity}.",
                    f"{action} an {identity} {noun}.",
                )
                for phrase in phrases:
                    with self.subTest(action=action, noun=noun, phrase=phrase):
                        self.assertDisclosureRejected(phrase)

    def test_reviewer_passive_created_identity_is_rejected(self):
        self.assertDisclosureRejected("An identity with AR" + "IN Online should be created.")

    def test_reviewer_passive_opened_profile_is_rejected(self):
        self.assertDisclosureRejected("A profile at AR" + "IN Online should be opened.")

    def test_passive_onboarding_preserves_encoded_and_control_decoding(self):
        identity = "AR" + "IN Online"
        phrases = (
            f"An identity with {identity} should be created.",
            f"A profile at {identity} should be opened.",
        )
        for phrase in phrases:
            variants = (
                quote(phrase, safe=""),
                base64.b64encode(phrase.encode()).decode(),
                phrase.replace(identity, "A\u200bR\x00IN Online"),
            )
            for variant in variants:
                with self.subTest(phrase=phrase, variant=variant):
                    self.assertProhibitedRejected(variant)

    def test_onboarding_action_morphology_is_rejected(self):
        identity = "AR" + "IN Online"
        phrases = (
            f"A user creates an account with {identity}.",
            f"Creating an account with {identity} is prohibited.",
            f"An account with {identity} was created.",
            f"A user opens a profile at {identity}.",
            f"Opening a profile at {identity} is prohibited.",
            f"A profile at {identity} was opened.",
            f"A user registers an identity with {identity}.",
            f"Registering an identity with {identity} is prohibited.",
            f"An identity with {identity} was registered.",
            f"A user starts an account with {identity}.",
            f"Starting an account with {identity} is prohibited.",
            f"An account with {identity} was started.",
            f"A user establishes an identity with {identity}.",
            f"Establishing an identity with {identity} is prohibited.",
            f"An identity with {identity} was established.",
            f"A user sets up a profile at {identity}.",
            f"Setting up a profile at {identity} is prohibited.",
            f"A profile at {identity} was set up.",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertDisclosureRejected(phrase)

    def test_registry_reordered_and_encoded_workflows_are_rejected(self):
        workflows = (
            "To sub" + "mit a resource application, first create an account with A" + "RIN Online.",
            "Open an A" + "RIN Online acc" + "ount before requesting the resource form.",
            quote("Sign " + "up with A" + "RIN Online, then submit a resource request.", safe=""),
            "Create an acc" + "ount with A" + "RIN Onl&#105;ne, then open a resource ticket.",
        )
        for workflow in workflows:
            with self.subTest(workflow=workflow):
                self.assertDisclosureRejected(workflow)

    def test_registry_workflow_synonym_matrix_is_rejected(self):
        identity = "AR" + "IN Online"
        workflows = (
            f"Register an account with {identity} before filing a resource request.",
            f"Set up a {identity} account, then submitting a resource application.",
            f"Create an account with {identity} before opening a resource form.",
            f"Sign up with {identity} before requesting resources.",
        )
        for workflow in workflows:
            with self.subTest(workflow=workflow):
                self.assertDisclosureRejected(workflow)

    def test_registry_semantics_do_not_cross_paragraphs(self):
        registry = "AR" + "IN"
        benign = (
            f"{registry} publishes public facts.\n\nA request is a general inquiry.\n\nContributors submit patches.",
            f"{registry} Online publishes public facts.\n\nA request is a general inquiry.\n\nContributors submit patches.",
        )
        for text in benign:
            with self.subTest(text=text):
                self.assertDisclosureAccepted(text)

    def test_reviewer_lone_cr_blank_line_is_a_paragraph_boundary(self):
        self.assertDisclosureAccepted("AR" + "IN Online is public.\r\rFile a resource request.")

    def test_reviewer_unicode_paragraph_separator_is_a_boundary(self):
        self.assertDisclosureAccepted("AR" + "IN Online is public.\u2029File a resource request.")

    def test_registry_workflow_boundary_matrix(self):
        paragraph_boundaries = {
            "lf-lf": "\n\n",
            "crlf-crlf": "\r\n\r\n",
            "cr-cr": "\r\r",
            "unicode-paragraph": "\u2029",
        }
        for name, boundary in paragraph_boundaries.items():
            with self.subTest(name=name):
                self.assertDisclosureAccepted("AR" + f"IN Online is public.{boundary}File a resource request.")
        self.assertDisclosureRejected("AR" + "IN Online is public.\u2028File a resource request.")

    def test_registry_semantics_do_not_cross_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            identity = "AR" + "IN Online"
            (root / "docs/decisions.md").write_text(f"{identity} is a public service.", encoding="utf-8")
            (root / "docs/publication.md").write_text("File a resource request.", encoding="utf-8")
            verify_repository(root, tracked_files=tracked)

    def test_adjacent_sentences_in_one_paragraph_form_a_resource_procedure(self):
        identity = "AR" + "IN Online"
        self.assertDisclosureRejected(f"{identity} is the registry portal. File a resource request.")
        self.assertDisclosureRejected(f"Submit the resource application. {identity} is the registry portal.")

    def test_nonadjacent_sentences_do_not_form_a_resource_procedure(self):
        identity = "AR" + "IN Online"
        self.assertDisclosureAccepted(
            f"{identity} is a public service. This sentence separates independent topics. File a resource request."
        )

    def test_legitimate_account_registry_and_ticket_prose_is_accepted(self):
        prose = (
            "Teams use generic accounts to track inventory.",
            "Readers can sign up with an unrelated online newsletter.",
            "ARIN Online is a public service operated by the regional registry.",
            "ARIN publishes public facts about Internet number resources.",
            "We opened a normal support ticket for a typo in this document.",
            "The security team reviews a generic application form.",
            "Contributors submit patches using the contribution workflow.",
            "Generic account guidance and public ARIN facts contain no operational steps.",
            "Readers can sign up for an unrelated newsletter; ARIN Online remains a public service.",
            "ARIN Online documents public registry facts; we opened a normal project ticket elsewhere.",
            "ARIN Online was created as a public informational service.",
            "The project profile was opened for an unrelated release; ARIN publishes public facts.",
        )
        for text in prose:
            with self.subTest(text=text):
                self.assertDisclosureAccepted(text)

    def test_concrete_nw_identifier_outside_cards_is_rejected(self):
        self.assertDisclosureRejected("Work item " + "NW" + "-99")

    def test_manifest_card_paths_are_the_only_structural_nw_exception(self):
        verify_repository(ROOT)

    def test_head_reader_ignores_worktree_bytes_but_publish_rejects_dirty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            self.init_repository(root)
            (root / "README.md").write_text("/" + "home" + "/someone/private", encoding="utf-8")
            verify_repository(root, source="head", require_clean=False)
            with self.assertRaisesRegex(SiteError, "disclosure"):
                verify_repository(root)
            with self.assertRaisesRegex(SiteError, "clean"):
                verify_publishable_repository(root)

    def test_publish_rejects_staged_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            self.init_repository(root)
            (root / "README.md").write_text((root / "README.md").read_text() + "\nchange\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            with self.assertRaisesRegex(SiteError, "clean"):
                verify_publishable_repository(root)

    def test_publish_rejects_unstaged_mode_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            self.init_repository(root)
            path = root / "README.md"
            path.chmod(path.stat().st_mode | 0o111)
            with self.assertRaisesRegex(SiteError, "clean"):
                verify_publishable_repository(root)

    def test_head_symlink_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            target = root / "README.md"
            target.unlink()
            target.symlink_to("AGENTS.md")
            self.init_repository(root)
            with self.assertRaisesRegex(SiteError, "regular"):
                verify_repository(root, source="head", require_clean=False)

    def test_committed_tracked_path_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_repository(root)
            (root / "extra.txt").write_text("public extra", encoding="utf-8")
            self.init_repository(root)
            with self.assertRaisesRegex(SiteError, "extra"):
                verify_repository(root, source="head", require_clean=False)

    def test_claude_instructions_import_agents_policy(self):
        self.assertEqual((ROOT / "CLAUDE.md").read_text(encoding="utf-8"), "# Claude Code instructions\n\n@AGENTS.md\n")

    def test_dockerfile_clears_base_html_before_copy(self):
        text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertLess(text.index("rm -rf /usr/share/nginx/html"), text.index("COPY --chown=101:101 site/"))

    def test_claude_settings_cover_local_reads_and_push_forms(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(set(settings), {"$schema", "permissions"})
        self.assertEqual(set(settings["permissions"]), {"deny", "ask", "allow"})
        denies = set(settings["permissions"]["deny"])
        for rule in (
            "Read(./CLAUDE.local.md)",
            "Read(./.claude/settings.local.json)",
            "Read(./.claude/kanban.lock.flock)",
            "Read(./.claude/kanban.lock.lockdir/**)",
            "Read(./.claude/kanban/grooming/TODO.md)",
            "Bash(git push:*)",
            "Bash(git -C * push:*)",
        ):
            self.assertIn(rule, denies)
        self.assertNotIn("Bash(git push --force:*)", denies)

    def test_publication_fails_closed_for_missing_decisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "publication.json"
            config.write_text(
                json.dumps({"provider": "", "correction_endpoint": "https://github.com/Xakki/net-watcher/issues"}),
                encoding="utf-8",
            )
            with self.assertRaises(PublicationError) as context:
                verify_publication(config)
        self.assertEqual(context.exception.errors, ["publication provider is missing"])

    def test_publication_rejects_placeholder_decisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "publication.json"
            config.write_text(json.dumps({"provider": "TBD", "correction_endpoint": "https://example.com"}), encoding="utf-8")
            with self.assertRaises(PublicationError) as context:
                verify_publication(config)
            self.assertIn("publication provider must be a final non-placeholder value", context.exception.errors)
            self.assertIn("correction endpoint must match the approved correction URL", context.exception.errors)

    def assertProhibitedRejected(self, payload: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            (root / "docs/decisions.md").write_text(payload, encoding="utf-8")
            with self.assertRaises(SiteError):
                verify_repository(root, tracked_files=tracked)

    def assertDisclosureRejected(self, payload: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            (root / "docs/decisions.md").write_text(payload, encoding="utf-8")
            with self.assertRaisesRegex(SiteError, "disclosure"):
                verify_repository(root, tracked_files=tracked)

    def assertDisclosureAccepted(self, payload: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracked = self.copy_repository(root)
            (root / "docs/decisions.md").write_text(payload, encoding="utf-8")
            verify_repository(root, tracked_files=tracked)


if __name__ == "__main__":
    unittest.main()
