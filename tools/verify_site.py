#!/usr/bin/env python3
import argparse
import base64
import binascii
import html
import html.parser
import json
import os
import re
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

MAX_FILE_BYTES = 300_000
MAX_TEXT_CODEPOINTS = 300_000
MAX_DECODE_ITERATIONS = 8
MAX_DECODE_VIEWS = 16
CANONICAL_HOST = "net.xakki.pro"
CORRECTION_ENDPOINT = "https://github.com/Xakki/net-watcher/issues"
PLACEHOLDERS = {"tbd", "todo", "unknown", "placeholder", "example", "n/a", "none"}
ALLOWED_HTML_FILES = {"index.html", "styles.css"}
ALLOWED_SITE_FILES = {"audit.md", *ALLOWED_HTML_FILES}
ALLOWED_SOURCE_SITE_FILES = set(ALLOWED_SITE_FILES)
REQUIRED_SECTION_IDS = {"status", "method", "clocks", "boundaries", "interpretation", "corrections"}
DISALLOWED_TAGS = {"script", "form", "input", "button", "textarea", "select", "iframe", "object", "embed", "video", "audio", "canvas"}
DISALLOWED_SITE_TERMS = {"analytics", "commercial customer", "customer data", "conversion", "marketing", "user tracking", "subject identifier", "raw report", "row-level", "api key", "access token"}
BOUNDARY_KEYS = {"tracked_files", "served_files", "ignored_local_patterns", "prohibited_classes"}
PROHIBITED_CLASSES = (
    "account or application procedures",
    "credentials and private keys",
    "host inventory and provider procedures",
    "inherited task identifiers and histories",
    "internal absolute paths and provenance",
    "private review identities or evidence",
    "raw row-level searchable or audit data",
    "restricted real or minimized-event data",
    "vendor or vulnerability evidence",
)
REGULAR_GIT_MODES = {"100644", "100755"}
CARD_PATH = re.compile(r"\.claude/kanban/(?:grooming|todo|progress|test|ready|done)/NW-[1-9][0-9]*-[a-z0-9]+(?:-[a-z0-9]+)*\.md")
STATIC_ESCAPE = re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}|\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})")
BASE64_TOKEN = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])")
SINGLE_URL_ATTRIBUTES = {
    "action",
    "background",
    "cite",
    "classid",
    "codebase",
    "data",
    "formaction",
    "href",
    "icon",
    "longdesc",
    "manifest",
    "poster",
    "profile",
    "src",
    "usemap",
    "xlink:href",
}
URL_LIST_ATTRIBUTES = {"archive", "attributionsrc", "ping"}
SRCSET_ATTRIBUTES = {"imagesrcset", "srcset"}
ASSET_URL_ATTRIBUTES = {
    "archive",
    "attributionsrc",
    "background",
    "classid",
    "codebase",
    "data",
    "icon",
    "imagesrcset",
    "manifest",
    "ping",
    "poster",
    "profile",
    "src",
    "srcset",
    "usemap",
}
ASCII_WHITESPACE = "\t\n\f\r "


class SiteError(ValueError):
    pass


class PublicationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _srcset_urls(value: str):
    position = 0
    while position < len(value):
        while position < len(value) and value[position] in ASCII_WHITESPACE + ",":
            position += 1
        if position == len(value):
            return
        start = position
        while position < len(value) and value[position] not in ASCII_WHITESPACE:
            position += 1
        candidate = value[start:position]
        trailing_commas = len(candidate) - len(candidate.rstrip(","))
        candidate = candidate.rstrip(",")
        if candidate:
            yield candidate
        if trailing_commas:
            continue
        parentheses = 0
        while position < len(value):
            char = value[position]
            position += 1
            if char == "(":
                parentheses += 1
            elif char == ")" and parentheses:
                parentheses -= 1
            elif char == "," and not parentheses:
                break


def _url_kind(value: str) -> str | None:
    canonical = value.strip(ASCII_WHITESPACE).replace("\\", "/")
    if not canonical:
        return "unsafe"
    try:
        parsed = urlparse(canonical)
    except ValueError:
        return "unsafe"
    if parsed.scheme:
        if parsed.scheme.casefold() not in {"http", "https"}:
            return "unsafe"
        return "external"
    if parsed.netloc or canonical.startswith("//"):
        return "external"
    return None


def _is_asset_url(tag: str, name: str) -> bool:
    return name in ASSET_URL_ATTRIBUTES or (
        name in {"href", "xlink:href"} and tag not in {"a", "area"}
    )


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
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            if raw_value is None:
                continue
            if name in SRCSET_ATTRIBUTES:
                urls = _srcset_urls(raw_value)
            elif name in URL_LIST_ATTRIBUTES:
                urls = iter(raw_value.split())
            elif name in SINGLE_URL_ATTRIBUTES:
                urls = iter((raw_value,))
            else:
                continue
            for url in urls:
                kind = _url_kind(url)
                if kind == "unsafe":
                    self.errors.append("unsafe URL is prohibited")
                elif kind == "external" and _is_asset_url(tag, name):
                    self.errors.append("external asset is prohibited")
        if tag == "meta" and (values.get("http-equiv") or "").casefold() == "refresh":
            self.errors.append("meta refresh is prohibited")
        if any(name.lower().startswith("on") for name, _ in attrs):
            self.errors.append("event handler attribute is prohibited")

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)


def _validate_relative(relative: str) -> tuple[str, ...]:
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise SiteError(f"invalid repository path: {relative}")
    return path.parts


def _decode_bounded(data: bytes, label: str) -> str:
    if len(data) > MAX_FILE_BYTES:
        raise SiteError(f"file exceeds size limit: {label}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SiteError(f"invalid UTF-8: {label}") from error
    _check_text_budget(text, label)
    for char in text:
        if unicodedata.category(char) in {"Cc", "Cf"} and char not in "\n\r\t":
            raise SiteError(f"prohibited Unicode control in {label}")
    return text


def _read_max_plus_one(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    remaining = MAX_FILE_BYTES + 1
    while remaining:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _check_text_budget(text: str, label: str = "decoded text") -> None:
    if len(text) > MAX_TEXT_CODEPOINTS or len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise SiteError(f"text exceeds decode budget: {label}")


class WorktreeReader:
    def __init__(self, root: Path):
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0)
        try:
            self.root_fd = os.open(root, flags)
        except OSError as error:
            raise SiteError("cannot open repository root") from error

    def close(self) -> None:
        os.close(self.root_fd)

    def read(self, relative: str) -> str:
        parts = _validate_relative(relative)
        descriptor = os.dup(self.root_fd)
        directory_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_DIRECTORY", 0)
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            for part in parts[:-1]:
                next_descriptor = os.open(part, directory_flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
                if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    raise SiteError(f"cannot open repository parent: {relative}")
            file_descriptor = os.open(parts[-1], file_flags, dir_fd=descriptor)
            try:
                if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
                    raise SiteError(f"not a regular file: {relative}")
                data = _read_max_plus_one(file_descriptor)
            finally:
                os.close(file_descriptor)
        except OSError as error:
            raise SiteError(f"cannot open regular file: {relative}") from error
        finally:
            os.close(descriptor)
        return _decode_bounded(data, relative)


class HeadReader:
    def __init__(self, root: Path):
        self.root = root
        try:
            result = subprocess.run(
                ["git", "ls-tree", "-rz", "--full-tree", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:
            raise SiteError("cannot read immutable HEAD tree") from error
        self.entries: dict[str, tuple[str, str, str]] = {}
        for record in result.stdout.split(b"\0"):
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8")
            self.entries[path] = (mode, object_type, object_id)

    def paths(self) -> set[str]:
        return set(self.entries)

    def read(self, relative: str) -> str:
        _validate_relative(relative)
        entry = self.entries.get(relative)
        if entry is None:
            raise SiteError(f"missing HEAD path: {relative}")
        mode, object_type, object_id = entry
        if mode not in REGULAR_GIT_MODES or object_type != "blob":
            raise SiteError(f"HEAD path is not a regular file: {relative}")
        process = subprocess.Popen(
            ["git", "cat-file", "blob", object_id],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        data = process.stdout.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            process.kill()
            process.wait()
            raise SiteError(f"file exceeds size limit: {relative}")
        remainder = process.stdout.read(1)
        stderr = process.communicate()[1]
        if remainder or process.returncode != 0:
            raise SiteError(f"cannot read HEAD object: {relative}: {stderr.decode(errors='replace').strip()}")
        return _decode_bounded(data, relative)


def read_bounded(path: Path) -> str:
    reader = WorktreeReader(path.parent)
    try:
        return reader.read(path.name)
    finally:
        reader.close()


def _consume_css_escape(text: str, position: int) -> tuple[str, int]:
    position += 1
    if position == len(text):
        return "", position
    if text[position] in "\n\f":
        return "", position + 1
    if text[position] == "\r":
        return "", position + 2 if text[position : position + 2] == "\r\n" else position + 1
    end = position
    while end < len(text) and end - position < 6 and text[end] in "0123456789abcdefABCDEF":
        end += 1
    if end > position:
        codepoint = int(text[position:end], 16)
        if end < len(text) and text[end] in ASCII_WHITESPACE:
            end += 1
        if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            return "\ufffd", end
        return chr(codepoint), end
    return text[position], position + 1


def _consume_css_string(text: str, position: int) -> tuple[str, int]:
    quote_char = text[position]
    position += 1
    result: list[str] = []
    while position < len(text):
        char = text[position]
        if char == quote_char:
            return "".join(result), position + 1
        if char in "\n\r\f":
            return "".join(result), position
        if char == "\\":
            decoded, position = _consume_css_escape(text, position)
            result.append(decoded)
        else:
            result.append(char)
            position += 1
    return "".join(result), position


def _skip_css_space_and_comments(text: str, position: int) -> int:
    while position < len(text):
        if text[position] in ASCII_WHITESPACE:
            position += 1
        elif text.startswith("/*", position):
            end = text.find("*/", position + 2)
            if end < 0:
                return len(text)
            position = end + 2
        else:
            return position
    return position


def _consume_css_name(text: str, position: int) -> tuple[str, int]:
    result: list[str] = []
    while position < len(text):
        char = text[position]
        if char.isalnum() or char in "-_" or ord(char) >= 128:
            result.append(char)
            position += 1
        elif char == "\\":
            decoded, position = _consume_css_escape(text, position)
            result.append(decoded)
        else:
            break
    return "".join(result), position


def _consume_css_url(text: str, position: int) -> tuple[str, int]:
    position = _skip_css_space_and_comments(text, position)
    if position < len(text) and text[position] in "'\"":
        value, position = _consume_css_string(text, position)
        position = _skip_css_space_and_comments(text, position)
        if position < len(text) and text[position] == ")":
            position += 1
        return value, position
    result: list[str] = []
    while position < len(text):
        char = text[position]
        if char == ")":
            return "".join(result).rstrip(ASCII_WHITESPACE), position + 1
        if char == "\\":
            decoded, position = _consume_css_escape(text, position)
            result.append(decoded)
        else:
            result.append(char)
            position += 1
    return "".join(result).rstrip(ASCII_WHITESPACE), position


def _css_urls(text: str):
    position = 0
    while position < len(text):
        if text.startswith("/*", position):
            position = _skip_css_space_and_comments(text, position)
            continue
        if text[position] in "'\"":
            _, position = _consume_css_string(text, position)
            continue
        if text[position] == "@":
            name, end = _consume_css_name(text, position + 1)
            if name.casefold() == "import":
                value_start = _skip_css_space_and_comments(text, end)
                if value_start < len(text) and text[value_start] in "'\"":
                    value, position = _consume_css_string(text, value_start)
                    yield value
                    continue
                function, function_end = _consume_css_name(text, value_start)
                if function.casefold() == "url" and function_end < len(text) and text[function_end] == "(":
                    value, position = _consume_css_url(text, function_end + 1)
                    yield value
                    continue
            position = max(end, position + 1)
            continue
        if text[position].isalnum() or text[position] in "-_\\" or ord(text[position]) >= 128:
            name, end = _consume_css_name(text, position)
            if name.casefold() == "url" and end < len(text) and text[end] == "(":
                value, position = _consume_css_url(text, end + 1)
                yield value
                continue
            position = max(end, position + 1)
            continue
        position += 1


def verify_site_content(html_text: str, css_text: str, actual: set[str]) -> None:
    if actual != ALLOWED_HTML_FILES:
        raise SiteError(f"site file set mismatch: {sorted(actual)}")
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
    for url in _css_urls(css_text):
        kind = _url_kind(url)
        if kind == "unsafe":
            errors.append("unsafe CSS asset is prohibited")
        elif kind == "external":
            errors.append("external CSS asset is prohibited")
    if errors:
        raise SiteError("; ".join(errors))


MARKDOWN_DISALLOWED_TAGS = {"script", "form", "input", "button", "textarea", "select", "iframe", "object", "embed"}
MARKDOWN_URL = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
MARKDOWN_HTML_TAG = re.compile(r"<\s*/?\s*([A-Za-z][A-Za-z0-9:-]*)\b[^>]*>")


def verify_markdown(markdown_text: str) -> None:
    """Validate future-served Markdown as inert, public-safe source content."""
    errors: list[str] = []
    lowered = markdown_text.casefold()
    parser = SiteParser()
    parser.feed(markdown_text)
    errors.extend(parser.errors)
    for match in MARKDOWN_HTML_TAG.finditer(markdown_text):
        if match.group(1).casefold() in MARKDOWN_DISALLOWED_TAGS:
            errors.append(f"prohibited {match.group(1).casefold()} element")
    for match in MARKDOWN_URL.finditer(markdown_text):
        url = match.group(1).strip()
        kind = _url_kind(url)
        if kind == "unsafe":
            errors.append("unsafe URL is prohibited")
        elif match.group(0).startswith("!") and kind == "external":
            errors.append("external asset is prohibited")
    if re.search(r"\b(?:on[a-z]+|javascript|data)\s*=", lowered):
        errors.append("active Markdown attribute is prohibited")
    if errors:
        raise SiteError("; ".join(errors))


def verify_site(site_dir: Path) -> None:
    if site_dir.is_symlink() or not site_dir.is_dir():
        raise SiteError("site must be a regular directory")
    reader = WorktreeReader(site_dir)
    try:
        actual = {entry.name for entry in os.scandir(site_dir)}
        if actual != ALLOWED_SOURCE_SITE_FILES:
            raise SiteError(f"site source file set mismatch: {sorted(actual)}")
        verify_site_content(reader.read("index.html"), reader.read("styles.css"), ALLOWED_HTML_FILES)
        verify_markdown(reader.read("audit.md"))
    finally:
        reader.close()


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SiteError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json(text: str) -> object:
    return json.loads(text, object_pairs_hook=_strict_object)


def _publication_errors(config: object) -> list[str]:
    if not isinstance(config, dict) or set(config) != {"provider", "correction_endpoint"}:
        return ["publication config must contain exactly provider and correction_endpoint"]
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
            errors.append("correction endpoint must match the approved correction URL")
    return errors


def verify_publication(config_path: Path) -> None:
    try:
        config = _parse_json(read_bounded(config_path))
    except (json.JSONDecodeError, SiteError) as error:
        raise PublicationError([f"invalid publication config: {error}"]) from error
    errors = _publication_errors(config)
    if errors:
        raise PublicationError(errors)


def _load_boundary(reader: WorktreeReader | HeadReader) -> dict:
    try:
        boundary = _parse_json(reader.read("publication-boundary.json"))
    except (json.JSONDecodeError, SiteError) as error:
        raise SiteError(f"invalid publication boundary: {error}") from error
    if not isinstance(boundary, dict) or set(boundary) != BOUNDARY_KEYS:
        raise SiteError("publication boundary keys are invalid")
    for key in BOUNDARY_KEYS:
        values = boundary[key]
        if not isinstance(values, list) or not values or not all(isinstance(value, str) for value in values):
            raise SiteError(f"publication boundary {key} must be a sorted unique non-empty list")
    if boundary["prohibited_classes"] != list(PROHIBITED_CLASSES):
        raise SiteError("publication boundary prohibited classes must exactly match the canonical contract")
    for key in BOUNDARY_KEYS - {"prohibited_classes"}:
        values = boundary[key]
        if values != sorted(set(values)):
            raise SiteError(f"publication boundary {key} must be a sorted unique non-empty list")
    return boundary


def load_boundary(root: Path) -> dict:
    reader = WorktreeReader(root)
    try:
        return _load_boundary(reader)
    finally:
        reader.close()


def git_tracked_files(root: Path) -> set[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True)
    return {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}


def _decode_static(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = next(group for group in match.groups() if group is not None)
        codepoint = int(raw, 16)
        if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            raise SiteError("invalid static Unicode escape")
        return chr(codepoint)

    return STATIC_ESCAPE.sub(replace, text)


def _normalize_once(text: str) -> str:
    stages = (html.unescape(text),)
    decoded = stages[-1]
    _check_text_budget(decoded)
    decoded = unquote(decoded, errors="strict")
    _check_text_budget(decoded)
    decoded = _decode_static(decoded)
    _check_text_budget(decoded)
    decoded = unicodedata.normalize("NFKC", decoded)
    _check_text_budget(decoded)
    return decoded


def _decode_fixpoint(text: str) -> str:
    current = text
    _check_text_budget(current)
    for _ in range(MAX_DECODE_ITERATIONS):
        updated = _normalize_once(current)
        if updated == current:
            return updated
        current = updated
    if _normalize_once(current) != current:
        raise SiteError("decode iteration limit exceeded")
    return current


def _structural_view(text: str) -> str:
    result = "".join(
        char
        for char in text
        if unicodedata.category(char) not in {"Cf", "Mn", "Me"}
        and (unicodedata.category(char) != "Cc" or char in "\n\r\t")
    )
    _check_text_budget(result)
    return result


def decoded_views(text: str):
    pending = [text]
    seen: set[str] = set()
    while pending:
        raw = pending.pop(0)
        decoded = _decode_fixpoint(raw)
        view = _structural_view(decoded.casefold())
        if view in seen:
            continue
        seen.add(view)
        if len(seen) > MAX_DECODE_VIEWS:
            raise SiteError("decode view limit exceeded")
        yield view
        for token in BASE64_TOKEN.findall(decoded):
            try:
                decoded = base64.b64decode(token, validate=True)
                decoded_text = decoded.decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                continue
            _check_text_budget(decoded_text)
            pending.append(decoded_text)


def _gitignore_patterns(text: str) -> list[str]:
    return sorted(line for line in text.splitlines() if line and not line.startswith("#") and not line.startswith("!"))


def _scan_text(relative: str, text: str) -> str:
    if relative == "publication-boundary.json":
        boundary = _parse_json(text)
        if isinstance(boundary, dict) and isinstance(boundary.get("tracked_files"), list):
            boundary = dict(boundary)
            boundary["tracked_files"] = ["<canonical-card-path>" if isinstance(value, str) and CARD_PATH.fullmatch(value) else value for value in boundary["tracked_files"]]
            return json.dumps(boundary, sort_keys=True)
    return text


def _is_card(relative: str) -> bool:
    return CARD_PATH.fullmatch(relative) is not None


def _paragraph_sentences(view: str):
    canonical = (
        view.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u2029", "\n\n")
        .replace("\u2028", "\n")
    )
    for paragraph in re.split(r"(?:\n[ \t]*){2,}", canonical):
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)|[;\n]+", paragraph)
            if sentence.strip()
        ]
        if sentences:
            yield sentences


def _contains_registry_operation(view: str) -> bool:
    registry_name = "ar" + "in"
    registry = re.compile(rf"\b{registry_name}\b")
    registry_online = re.compile(rf"\b{registry_name}\s+online\b")
    account_domain = re.compile(rf"account\s*\.\s*{registry_name}\s*\.\s*net")
    signup = re.compile(r"\b(?:signup|sign[\s-]+up|enroll|enrol)\b")
    identity_noun = re.compile(r"\b(?:accounts?|identit(?:y|ies)|profiles?)\b")
    identity_action = re.compile(
        r"\b(?:creat(?:e(?:s|d)?|ing)|open(?:s|ed|ing)?|register(?:s|ed|ing)?|"
        r"start(?:s|ed|ing)?|establish(?:es|ed|ing)?|set(?:s|ting)?\s+up)\b"
    )
    resource_action = re.compile(
        r"\b(?:file|filing|lodge|lodging|submit|submitting|open|opening|request|requesting|apply|applying)\b"
    )
    resource_target = re.compile(r"\b(?:resources?|resource\s+(?:requests?|tickets?|forms?|applications?))\b")
    workflow_noun = re.compile(r"\b(?:request|application|submission)\b")
    workflow_action = re.compile(r"\b(?:forms?|workflows?|process|instructions?|portal|procedure|file|submit|apply)\b")

    def has_onboarding(sentence: str) -> bool:
        if not registry_online.search(sentence):
            return False
        return signup.search(sentence) is not None or (
            identity_action.search(sentence) is not None and identity_noun.search(sentence) is not None
        )

    def has_resource_workflow(sentence: str) -> bool:
        return (
            resource_action.search(sentence) is not None and resource_target.search(sentence) is not None
        ) or (
            workflow_noun.search(sentence) is not None and workflow_action.search(sentence) is not None
        )

    for sentences in _paragraph_sentences(view):
        if any(account_domain.search(sentence) or has_onboarding(sentence) for sentence in sentences):
            return True
        for index, sentence in enumerate(sentences):
            if registry.search(sentence) and has_resource_workflow(sentence):
                return True
            if index + 1 < len(sentences):
                adjacent = sentences[index + 1]
                if (registry.search(sentence) and has_resource_workflow(adjacent)) or (
                    has_resource_workflow(sentence) and registry.search(adjacent)
                ):
                    return True
    return False


def _verify_repository_reader(reader: WorktreeReader | HeadReader, actual: set[str]) -> None:
    boundary = _load_boundary(reader)
    expected = set(boundary["tracked_files"])
    if actual != expected:
        raise SiteError(f"tracked publication set mismatch; missing={sorted(expected - actual)}; extra={sorted(actual - expected)}")
    if set(boundary["served_files"]) != {"site/audit.md", "site/index.html", "site/styles.css"}:
        raise SiteError("served publication set mismatch")
    ignored = _gitignore_patterns(reader.read(".gitignore"))
    if boundary["ignored_local_patterns"] != ignored:
        raise SiteError("ignored-local manifest does not exactly match .gitignore")

    concrete_local_id = re.compile(r"\bNW-[1-9][0-9]*\b", re.IGNORECASE)
    foreign_ids = re.compile(r"\b(?:EPIC|TASK|TICKET|MYIP|ARIN)[-_ ]?\d+\b", re.IGNORECASE)
    machine_paths = re.compile(r"/(?:home|users|workspace)/[^\s'\"<>]+", re.IGNORECASE)
    credential = re.compile(r"\b(?:gh[pousr]|github_pat)_[a-z0-9_]{20,}", re.IGNORECASE)
    sha = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)
    legacy_sensitive = re.compile(r"(?:registration\s+url|applicant\s+evidence|submission\s+instructions)", re.IGNORECASE)
    errors: list[str] = []
    for relative in sorted(expected):
        text = _scan_text(relative, reader.read(relative))
        for index, view in enumerate(decoded_views(text)):
            label = "encoded disclosure" if index else "disclosure"
            detected = (
                foreign_ids.search(view)
                or machine_paths.search(view)
                or credential.search(view)
                or sha.search(view)
                or _contains_registry_operation(view)
                or legacy_sensitive.search(view)
                or (not _is_card(relative) and concrete_local_id.search(view))
            )
            if detected or "-----begin " + "private key-----" in view:
                errors.append(f"{label} found in {relative}")
                break
    if errors:
        raise SiteError("; ".join(errors))


def _require_clean(root: Path) -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    if result.stdout:
        raise SiteError("publication requires a clean index and worktree")


def verify_repository(
    root: Path,
    tracked_files: set[str] | None = None,
    source: str = "worktree",
    require_clean: bool = False,
) -> None:
    if require_clean:
        _require_clean(root)
    if source == "head":
        reader = HeadReader(root)
        actual = reader.paths() if tracked_files is None else set(tracked_files)
        _verify_repository_reader(reader, actual)
        return
    if source != "worktree":
        raise SiteError(f"unsupported repository source: {source}")
    reader = WorktreeReader(root)
    try:
        actual = git_tracked_files(root) if tracked_files is None else set(tracked_files)
        _verify_repository_reader(reader, actual)
    finally:
        reader.close()


def verify_publishable_repository(root: Path) -> HeadReader:
    _require_clean(root)
    reader = HeadReader(root)
    _verify_repository_reader(reader, reader.paths())
    return reader


def verify_publishable_site(reader: HeadReader) -> None:
    """Validate every file that the immutable publication boundary serves."""
    verify_site_content(reader.read("site/index.html"), reader.read("site/styles.css"), ALLOWED_HTML_FILES)
    verify_markdown(reader.read("site/audit.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Net Watcher static publication boundary.")
    parser.add_argument("--publish", action="store_true", help="require final publication decisions from immutable HEAD")
    parser.add_argument("--repository", action="store_true", help="scan the tracked public repository")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.publish:
            reader = verify_publishable_repository(root)
            verify_publishable_site(reader)
            config = _parse_json(reader.read("publication.json"))
            errors = _publication_errors(config)
            if errors:
                raise PublicationError(errors)
        else:
            verify_site(root / "site")
            if args.repository:
                verify_repository(root)
    except (SiteError, PublicationError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"verification failed: {error}", file=sys.stderr)
        return 1
    print("verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
