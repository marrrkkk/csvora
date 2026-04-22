import csv


def detect_encoding(file_bytes: bytes) -> tuple[str, list[str]]:
    warnings: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            file_bytes.decode(encoding)
            if encoding != "utf-8-sig":
                warnings.append(f"Encoding fallback used: {encoding}")
            return encoding, warnings
        except UnicodeDecodeError:
            continue
    warnings.append("Could not reliably detect encoding, using latin-1")
    return "latin-1", warnings


def detect_delimiter(text: str, sample_lines: int) -> str:
    lines = [line for line in text.splitlines() if line.strip()][:sample_lines]
    sample = "\n".join(lines) if lines else text[:1000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except csv.Error:
        return ","


def detect_header_row(lines: list[str], delimiter: str) -> int:
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        cells = [cell.strip() for cell in line.split(delimiter)]
        non_empty = [cell for cell in cells if cell]
        if not non_empty:
            continue
        alpha_ratio = sum(cell.replace("_", "").replace("-", "").isalpha() for cell in non_empty) / len(non_empty)
        if alpha_ratio >= 0.5:
            return idx
        return idx
    return 0
