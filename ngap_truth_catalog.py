import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from pathlib import Path


TRUTH_XLSX_PATH = Path("/Users/raph/Downloads/presentation-nouvelle-cotation-masseur-kinesitherapeute.xlsx")
TRUTH_PDF_PATH = Path("/Users/raph/Downloads/NGAP vrai 2026 -23022026.pdf")
XML_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CATALOG_ALIASES = {
    "lca": "ligament croise anterieur",
    "ptg": "prothese genou",
    "pth": "prothese hanche",
    "bpco": "bronchopneumopathie chronique obstructive",
    "menisque": "meniscectomie",
    "lymphoedeme": "lymphodeme",
}


def _strip_accents(value: str | None) -> str:
    value = value or ""
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value.lower())
        if unicodedata.category(char) != "Mn"
    )


def normalize_catalog_text(value: str) -> str:
    value = _strip_accents(value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    for source, target in CATALOG_ALIASES.items():
        value = re.sub(rf"\b{re.escape(source)}\b", target, value)
    return value


def _shared_strings_from_archive(archive: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    shared_strings = []
    for si in root.findall("a:si", XML_NS):
        parts = []
        for text_node in si.iterfind(".//a:t", XML_NS):
            parts.append(text_node.text or "")
        shared_strings.append("".join(parts))
    return shared_strings


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value_node = cell.find("a:v", XML_NS)
    if value_node is None:
        return ""
    value = value_node.text or ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(value)]
    return value


def _build_search_blob(item: dict) -> str:
    values = [
        item.get("libelle", ""),
        item.get("theme", ""),
        item.get("sous_division", ""),
    ]
    return normalize_catalog_text(" ".join(value for value in values if value))


def _build_priority_blob(item: dict) -> str:
    values = [
        item.get("libelle", ""),
        item.get("sous_division", ""),
    ]
    return normalize_catalog_text(" ".join(value for value in values if value))


def _format_cotation(item: dict) -> str:
    lettre = (item.get("lettre_cle") or "").strip()
    valeur = str(item.get("cotation_valeur") or "").strip()
    return f"{lettre} {valeur}".strip()


def _extract_entries_from_xlsx(xlsx_path: Path) -> list[dict]:
    with zipfile.ZipFile(xlsx_path) as archive:
        shared_strings = _shared_strings_from_archive(archive)
        worksheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    current_theme = ""
    current_libelle = ""
    current_sous_division = ""
    entries = []

    for row in worksheet.findall("a:sheetData/a:row", XML_NS):
        cells = {
            cell.attrib["r"][:1]: _cell_value(cell, shared_strings).strip()
            for cell in row.findall("a:c", XML_NS)
            if cell.attrib.get("r")
        }
        theme = cells.get("E", "").strip()
        libelle = cells.get("F", "").strip()
        sous_division = cells.get("G", "").strip()
        lettre_cle = cells.get("H", "").strip()
        cotation = cells.get("I", "").strip()

        if theme:
            current_theme = theme
        if libelle:
            current_libelle = libelle
            current_sous_division = ""
        if sous_division:
            current_sous_division = sous_division

        if not lettre_cle or not cotation:
            continue
        if not re.fullmatch(r"[A-Z ]+", lettre_cle) or not re.fullmatch(r"\d+(?:\.\d+)?", cotation):
            continue

        entry = {
            "ID": len(entries) + 1,
            "theme": current_theme,
            "libelle": current_libelle,
            "sous_division": sous_division or current_sous_division or None,
            "lettre_cle": lettre_cle,
            "cotation_valeur": cotation,
            "cotation": _format_cotation({"lettre_cle": lettre_cle, "cotation_valeur": cotation}),
            "search_blob": "",
            "priority_blob": "",
            "source_xlsx": str(xlsx_path),
            "source_pdf": str(TRUTH_PDF_PATH),
        }
        entry["search_blob"] = _build_search_blob(entry)
        entry["priority_blob"] = _build_priority_blob(entry)
        entries.append(entry)

    return entries


@lru_cache(maxsize=1)
def load_truth_catalog() -> list[dict]:
    if not TRUTH_XLSX_PATH.exists():
        raise FileNotFoundError(f"Fichier source introuvable: {TRUTH_XLSX_PATH}")
    return _extract_entries_from_xlsx(TRUTH_XLSX_PATH)


def search_truth_catalog(query: str, limit: int = 3) -> list[dict]:
    normalized_query = normalize_catalog_text(query)
    if not normalized_query:
        return []

    query_tokens = set(normalized_query.split())
    scored = []

    for item in load_truth_catalog():
        haystack = item["search_blob"]
        priority_blob = item["priority_blob"]
        haystack_tokens = set(haystack.split())
        priority_tokens = set(priority_blob.split())
        token_overlap = len(query_tokens & haystack_tokens)
        priority_overlap = len(query_tokens & priority_tokens)
        phrase_bonus = 6 if normalized_query in haystack else 0
        score = token_overlap + (priority_overlap * 2) + phrase_bonus
        if score <= 0:
            continue
        scored.append((score, item))

    scored.sort(
        key=lambda pair: (
            -pair[0],
            pair[1].get("theme", ""),
            pair[1].get("libelle", ""),
            pair[1].get("sous_division") or "",
        )
    )
    return [item for _, item in scored[:limit]]
