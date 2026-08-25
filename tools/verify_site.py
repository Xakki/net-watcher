#!/usr/bin/env python3
import argparse
import html.parser
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

MAX_FILE_BYTES = 300_000
MAX_TEXT_CODEPOINTS = 300_000
CANONICAL_HOST = "net.xakki.pro"
CORRECTION_ENDPOINT = "https://github.com/Xakki/net-watcher/issues"
PLACEHOLDERS = {"tbd", "todo", "unknown", "placeholder", "example", "n/a", "none"}
ALLOWED_SITE_FILES = {"index.html", "styles.css"}
REQUIRED_SECTION_IDS = {"status", "method", "clocks", "boundaries", "interpretation", "corrections"}
DISALLOWED_TAGS = {"script", "form", "input", "button", "textarea", "select", "iframe", "object", "embed", "video", "audio", "canvas"}
DISALLOWED_SITE_TERMS = {
    "analytics",
    "commercial",
    "commercial customer",
    "customer data",
    "conversion",
    "marketing",
    "product",
    "user tracking",
    "subject identifier",
    "raw report",
    "row-level",
    "api key",
    "access token",
}
REPOSITORY_FILES = {
    ".dockerignore", ".env.example", ".gitignore", "CONTRIBUTING.md", "DEPLOY.md", "Dockerfile",
    "LICENSE", "Makefile", "README.md", "SECURITY.md", "compose.yaml", "nginx.conf", "publication.json",
    "site/index.html", "site/styles.css", "tests/__init__.py", "tests/test_verify_site.py", "tools/__init__.py",
    "tools/verify_site.py", "docs/ports.md", ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/methodology.yml",
    ".github/ISSUE_TEMPLATE/privacy-disclosure.yml", ".github/ISSUE_TEMPLATE/research-correction.yml",
}


class SiteError(ValueError):
    pass


class PublicationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class SiteParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.lang = ""
        self.text_parts: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in DISALLOWED_TAGS:
            self.errors.append(f"prohibited {tag} element")
        if tag == "html":
            self.lang = values.get("lang", "") or ""
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if values.get("style"):
            self.errors.append("inline style is prohibited")
        if tag in {"img", "source", "link"}:
            asset = values.get("src") or values.get("href") or ""
            parsed = urlparse(asset)
            if parsed.scheme or parsed.netloc or asset.startswith("//"):
                self.errors.append("external asset is prohibited")
        if any(name.lower().startswith("on") for name, _ in attrs):
            self.errors.append("event handler attribute is prohibited")

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)



def read_bounded(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise SiteError(f"not a regular file: {path.name}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise SiteError(f"file exceeds size limit: {path.name}")
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SiteError(f"invalid UTF-8: {path.name}") from error
    if len(text) > MAX_TEXT_CODEPOINTS:
        raise SiteError(f"text exceeds code point limit: {path.name}")
    for char in text:
        category = unicodedata.category(char)
        if category in {"Cc", "Cf"} and char not in "\n\r\t":
            raise SiteError(f"prohibited Unicode control in {path.name}")
    return text



def verify_site(site_dir: Path) -> None:
    if site_dir.is_symlink() or not site_dir.is_dir():
        raise SiteError("site must be a regular directory")
    actual = {path.name for path in site_dir.iterdir()}
    if actual != ALLOWED_SITE_FILES:
        raise SiteError(f"site file set mismatch: {sorted(actual)}")
    html_text = read_bounded(site_dir / "index.html")
    css_text = read_bounded(site_dir / "styles.css")
    parser = SiteParser()
    parser.feed(html_text)
    errors = list(parser.errors)
    if parser.lang != "en":
        errors.append("document language must be English")
    missing = sorted(REQUIRED_SECTION_IDS - parser.ids)
    if missing:
        errors.append(f"required sections missing: {', '.join(missing)}")
    visible = " ".join(" ".join(parser.text_parts).split())
    normalized = unicodedata.normalize("NFKC", html_text + "\n" + css_text).casefold()
    for required in ("net watcher", CANONICAL_HOST, "no results are published", "observational", "cannot establish cause", "publicly available", "synthetic"):
        if required not in normalized:
            errors.append(f"required declaration missing: {required}")
    for term in sorted(DISALLOWED_SITE_TERMS):
        if term in normalized:
            errors.append(f"prohibited public content: {term}")
    if re.search(r"\b(?:epic|task|ticket)[-_ ]?\d+", normalized):
        errors.append("internal metadata is prohibited")
    if "<table" in normalized or re.search(r"\b\d+(?:\.\d+)?%\b", visible):
        errors.append("results-like presentation is prohibited")
    if re.search(r"url\s*\(\s*['\"]?(?:https?:)?//", css_text, re.IGNORECASE):
        errors.append("external CSS asset is prohibited")
    if errors:
        raise SiteError("; ".join(errors))



def verify_publication(config_path: Path) -> None:
    try:
        config = json.loads(read_bounded(config_path))
    except (json.JSONDecodeError, SiteError) as error:
        raise PublicationError([f"invalid publication config: {error}"]) from error
    if not isinstance(config, dict) or set(config) != {"provider", "correction_endpoint"}:
        raise PublicationError(["publication config must contain exactly provider and correction_endpoint"])
    errors: list[str] = []
    provider = config.get("provider")
    if provider is None or (isinstance(provider, str) and not provider.strip()):
        errors.append("publication provider is missing")
    elif not isinstance(provider, str) or provider.strip().casefold() in PLACEHOLDERS or len(provider.strip()) > 120:
        errors.append("publication provider must be a final non-placeholder value")
    endpoint = config.get("correction_endpoint")
    if endpoint is None or (isinstance(endpoint, str) and not endpoint.strip()):
        errors.append("correction endpoint is missing")
    elif not isinstance(endpoint, str) or endpoint.strip().casefold() in PLACEHOLDERS:
        errors.append("correction endpoint must be a final non-placeholder HTTPS URL")
    else:
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
            errors.append("correction endpoint must be a clean HTTPS URL")
        elif endpoint != CORRECTION_ENDPOINT:
            errors.append("correction endpoint must use the canonical host or its subdomain")
    if errors:
        raise PublicationError(errors)



def verify_repository(root: Path) -> None:
    actual: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/") or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            raise SiteError(f"repository symlink is prohibited: {relative}")
        if path.is_file():
            actual.add(relative)
    if actual != REPOSITORY_FILES:
        missing = sorted(REPOSITORY_FILES - actual)
        extra = sorted(actual - REPOSITORY_FILES)
        raise SiteError(f"repository file set mismatch; missing={missing}; extra={extra}")
    disclosure_patterns = {
        "credential-shaped token": re.compile(r"(?i)\b(?:gh[pousr]|github_pat)_[a-z0-9_]{20,}"),
        "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "machine path": re.compile(r"/(?:home|users)/[A-Za-z0-9._-]+/"),
        "internal lifecycle identifier": re.compile(r"(?i)\b(?:epic|task|ticket)[-_ ]?\d{2,}"),
    }
    errors: list[str] = []
    for relative in sorted(actual):
        text = read_bounded(root / relative)
        for label, pattern in disclosure_patterns.items():
            if pattern.search(text):
                errors.append(f"{label} found in {relative}")
    if errors:
        raise SiteError("; ".join(errors))



def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Net Watcher static publication boundary.")
    parser.add_argument("--publish", action="store_true", help="require final publication decisions")
    parser.add_argument("--repository", action="store_true", help="scan the complete public repository")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        verify_site(root / "site")
        if args.repository:
            verify_repository(root)
        if args.publish:
            verify_publication(root / "publication.json")
    except (SiteError, PublicationError) as error:
        print(f"verification failed: {error}", file=sys.stderr)
        return 1
    print("verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
