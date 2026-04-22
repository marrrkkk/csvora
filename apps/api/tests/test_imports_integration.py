from tests.helpers import poll


def test_full_import_flow(client_inprocess, fixtures_dir) -> None:
    client = client_inprocess
    create = client.post("/api/v1/imports", json={})
    assert create.status_code == 201
    import_id = create.json()["id"]

    csv_path = fixtures_dir / "contacts_sample.csv"
    with csv_path.open("rb") as f:
        upload = client.post(
            f"/api/v1/imports/{import_id}/upload",
            files={"file": ("contacts_sample.csv", f, "text/csv")},
        )
    assert upload.status_code == 200

    analyze = client.post(f"/api/v1/imports/{import_id}/analyze")
    assert analyze.status_code == 200

    def analyzed():
        status = client.get(f"/api/v1/imports/{import_id}/status")
        if status.status_code != 200:
            return None
        if status.json()["status"] == "analyzed":
            return status.json()
        return None

    assert poll(analyzed, timeout_s=30.0, interval_s=1.0) is not None

    transform_payload = {
        "mappings": [
            {"source_column": "first_name", "target_field": "first_name"},
            {"source_column": "last_name", "target_field": "last_name"},
            {"source_column": "email", "target_field": "email"},
            {"source_column": "phone", "target_field": "phone"},
        ]
    }
    transform = client.post(f"/api/v1/imports/{import_id}/transform", json=transform_payload)
    assert transform.status_code == 200

    def completed():
        status = client.get(f"/api/v1/imports/{import_id}/status")
        if status.status_code != 200:
            return None
        if status.json()["status"] == "completed":
            return status.json()
        return None

    assert poll(completed, timeout_s=30.0, interval_s=1.0) is not None

    result = client.get(f"/api/v1/imports/{import_id}/result")
    assert result.status_code == 200
    body = result.json()
    assert body["valid_row_count"] >= 1
    assert body["cleaned_csv_key"]
    assert body["normalized_json_key"]
    assert body["validation_report_key"]


def test_import_isolation_between_api_keys(client_inprocess, second_client_inprocess) -> None:
    client = client_inprocess
    second_client = second_client_inprocess
    create = client.post("/api/v1/imports", json={})
    assert create.status_code == 201
    import_id = create.json()["id"]

    forbidden = second_client.get(f"/api/v1/imports/{import_id}")
    assert forbidden.status_code == 404


def test_duplicate_analyze_trigger_rejected(client_inprocess, fixtures_dir) -> None:
    client = client_inprocess
    create = client.post("/api/v1/imports", json={})
    assert create.status_code == 201
    import_id = create.json()["id"]

    csv_path = fixtures_dir / "contacts_sample.csv"
    with csv_path.open("rb") as f:
        upload = client.post(
            f"/api/v1/imports/{import_id}/upload",
            files={"file": ("contacts_sample.csv", f, "text/csv")},
        )
    assert upload.status_code == 200

    first = client.post(f"/api/v1/imports/{import_id}/analyze")
    assert first.status_code == 200
    second = client.post(f"/api/v1/imports/{import_id}/analyze")
    assert second.status_code == 409


def test_duplicate_transform_trigger_rejected(client_inprocess, fixtures_dir) -> None:
    client = client_inprocess
    create = client.post("/api/v1/imports", json={})
    assert create.status_code == 201
    import_id = create.json()["id"]

    csv_path = fixtures_dir / "contacts_sample.csv"
    with csv_path.open("rb") as f:
        upload = client.post(
            f"/api/v1/imports/{import_id}/upload",
            files={"file": ("contacts_sample.csv", f, "text/csv")},
        )
    assert upload.status_code == 200

    analyze = client.post(f"/api/v1/imports/{import_id}/analyze")
    assert analyze.status_code == 200

    def analyzed():
        status = client.get(f"/api/v1/imports/{import_id}/status")
        if status.status_code != 200:
            return None
        if status.json()["status"] == "analyzed":
            return status.json()
        return None

    assert poll(analyzed, timeout_s=30.0, interval_s=1.0) is not None

    payload = {
        "mappings": [
            {"source_column": "first_name", "target_field": "first_name"},
            {"source_column": "last_name", "target_field": "last_name"},
            {"source_column": "email", "target_field": "email"},
            {"source_column": "phone", "target_field": "phone"},
        ]
    }
    first = client.post(f"/api/v1/imports/{import_id}/transform", json=payload)
    assert first.status_code == 200
    second = client.post(f"/api/v1/imports/{import_id}/transform", json=payload)
    assert second.status_code == 409


def test_transform_rejects_duplicate_target_fields(client_inprocess, fixtures_dir) -> None:
    client = client_inprocess
    create = client.post("/api/v1/imports", json={})
    assert create.status_code == 201
    import_id = create.json()["id"]

    csv_path = fixtures_dir / "contacts_sample.csv"
    with csv_path.open("rb") as f:
        upload = client.post(
            f"/api/v1/imports/{import_id}/upload",
            files={"file": ("contacts_sample.csv", f, "text/csv")},
        )
    assert upload.status_code == 200

    analyze = client.post(f"/api/v1/imports/{import_id}/analyze")
    assert analyze.status_code == 200

    bad_payload = {
        "mappings": [
            {"source_column": "first_name", "target_field": "first_name"},
            {"source_column": "name", "target_field": "first_name"},
        ]
    }
    response = client.post(f"/api/v1/imports/{import_id}/transform", json=bad_payload)
    assert response.status_code == 422


def test_analyze_malformed_csv_transitions_to_failed(client_inprocess, fixtures_dir) -> None:
    client = client_inprocess
    create = client.post("/api/v1/imports", json={})
    assert create.status_code == 201
    import_id = create.json()["id"]

    csv_path = fixtures_dir / "malformed.csv"
    with csv_path.open("rb") as f:
        upload = client.post(
            f"/api/v1/imports/{import_id}/upload",
            files={"file": ("malformed.csv", f, "text/csv")},
        )
    assert upload.status_code == 200

    trigger = client.post(f"/api/v1/imports/{import_id}/analyze")
    assert trigger.status_code == 200

    def finished():
        status = client.get(f"/api/v1/imports/{import_id}/status")
        if status.status_code != 200:
            return None
        if status.json()["status"] in {"analyzed", "failed"}:
            return status.json()["status"]
        return None

    final_status = poll(finished, timeout_s=30.0, interval_s=1.0)
    assert final_status == "failed"


def test_create_import_requires_template_when_configured(client_inprocess, monkeypatch) -> None:
    monkeypatch.setenv("IMPORT_REQUIRES_TEMPLATE", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        r = client_inprocess.post("/api/v1/imports", json={})
        assert r.status_code == 400
        msg = (r.json().get("error") or {}).get("message", "")
        assert "template_id" in str(msg).lower()
    finally:
        monkeypatch.delenv("IMPORT_REQUIRES_TEMPLATE", raising=False)
        get_settings.cache_clear()

