from datetime import UTC, datetime
from uuid import UUID


def build_source_file_key(import_id: UUID, filename: str) -> str:
    safe_name = filename.replace("\\", "_").replace("/", "_").strip() or "upload.csv"
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"imports/{import_id}/source/{timestamp}_{safe_name}"


def build_analysis_file_key(import_id: UUID) -> str:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"imports/{import_id}/analysis/{timestamp}_analysis.json"


def build_output_file_keys(import_id: UUID) -> dict[str, str]:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    base = f"imports/{import_id}/outputs/{timestamp}"
    return {
        "cleaned_csv_key": f"{base}_cleaned.csv",
        "normalized_json_key": f"{base}_normalized.json",
        "validation_report_key": f"{base}_validation_report.json",
    }
