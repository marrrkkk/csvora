import uuid

from tests.helpers import poll


def _minimal_template_payload(slug_suffix: str | None = None):
    suf = slug_suffix or str(uuid.uuid4())[:8]
    return {
        "name": "Contacts default",
        "slug": f"contacts-default-{suf}",
        "description": "Integration test template",
        "schema_type": "contacts",
        "status": "active",
        "version": {
            "strict_mode": False,
            "auto_accept_confidence": 0.85,
            "review_threshold": 0.6,
            "ai_enabled": False,
            "fields": [
                {
                    "field_key": "first_name",
                    "label": "First name",
                    "value_type": "string",
                    "is_builtin": True,
                    "is_required": False,
                    "aliases": ["firstname", "given name"],
                    "allow_empty": True,
                    "sort_order": 0,
                },
                {
                    "field_key": "last_name",
                    "label": "Last name",
                    "value_type": "string",
                    "is_builtin": True,
                    "is_required": False,
                    "aliases": ["lastname", "surname"],
                    "allow_empty": True,
                    "sort_order": 1,
                },
                {
                    "field_key": "email",
                    "label": "Email",
                    "value_type": "email",
                    "is_builtin": True,
                    "is_required": False,
                    "aliases": ["e-mail", "mail"],
                    "allow_empty": True,
                    "sort_order": 2,
                },
                {
                    "field_key": "phone",
                    "label": "Phone",
                    "value_type": "phone",
                    "is_builtin": True,
                    "is_required": False,
                    "aliases": ["mobile", "tel"],
                    "allow_empty": True,
                    "sort_order": 3,
                },
            ],
        },
    }


def test_template_accepts_non_contact_schema_type(client_inprocess) -> None:
    payload = _minimal_template_payload("products")
    payload["slug"] = f"products-{uuid.uuid4().hex[:8]}"
    payload["schema_type"] = "products"
    payload["version"]["fields"] = [
        {
            "field_key": "sku",
            "label": "SKU",
            "value_type": "string",
            "is_builtin": False,
            "is_required": True,
            "aliases": [],
            "allow_empty": False,
            "sort_order": 0,
        },
        {
            "field_key": "title",
            "label": "Title",
            "value_type": "string",
            "is_builtin": False,
            "is_required": False,
            "aliases": [],
            "allow_empty": True,
            "sort_order": 1,
        },
    ]
    create = client_inprocess.post("/api/v1/templates", json=payload)
    assert create.status_code == 201, create.text
    assert create.json()["schema_type"] == "products"


def test_patch_template_schema_type(client_inprocess) -> None:
    payload = _minimal_template_payload("patch-schema")
    payload["slug"] = f"contacts-patch-schema-{uuid.uuid4().hex[:8]}"
    create = client_inprocess.post("/api/v1/templates", json=payload)
    assert create.status_code == 201, create.text
    tid = create.json()["id"]
    assert create.json()["schema_type"] == "contacts"

    patch = client_inprocess.patch(f"/api/v1/templates/{tid}", json={"schema_type": "customers"})
    assert patch.status_code == 200, patch.text
    assert patch.json()["schema_type"] == "customers"


def test_template_crud_and_list(client_inprocess) -> None:
    payload = _minimal_template_payload("crud")
    create = client_inprocess.post("/api/v1/templates", json=payload)
    assert create.status_code == 201, create.text
    tid = create.json()["id"]

    listed = client_inprocess.get("/api/v1/templates")
    assert listed.status_code == 200
    assert any(t["id"] == tid for t in listed.json())

    got = client_inprocess.get(f"/api/v1/templates/{tid}")
    assert got.status_code == 200
    assert got.json()["slug"] == "contacts-default-crud"

    patch = client_inprocess.patch(f"/api/v1/templates/{tid}", json={"name": "Renamed"})
    assert patch.status_code == 200
    assert patch.json()["name"] == "Renamed"

    arch = client_inprocess.post(f"/api/v1/templates/{tid}/archive")
    assert arch.status_code == 200
    assert arch.json()["status"] == "archived"


def test_template_import_auto_transform(client_inprocess, fixtures_dir) -> None:
    payload = _minimal_template_payload("auto")
    payload["slug"] = f"contacts-auto-{uuid.uuid4().hex[:8]}"
    t = client_inprocess.post("/api/v1/templates", json=payload)
    assert t.status_code == 201, t.text
    template_id = t.json()["id"]

    imp = client_inprocess.post("/api/v1/imports", json={"template_id": template_id})
    assert imp.status_code == 201, imp.text
    import_id = imp.json()["id"]
    assert imp.json()["template_id"] == template_id

    csv_path = fixtures_dir / "contacts_sample.csv"
    with csv_path.open("rb") as f:
        up = client_inprocess.post(
            f"/api/v1/imports/{import_id}/upload",
            files={"file": ("contacts_sample.csv", f, "text/csv")},
        )
    assert up.status_code == 200

    an = client_inprocess.post(f"/api/v1/imports/{import_id}/analyze")
    assert an.status_code == 200

    def ready():
        st = client_inprocess.get(f"/api/v1/imports/{import_id}/status")
        if st.status_code != 200:
            return None
        j = st.json()
        if j["status"] in ("ready_to_transform", "needs_review", "analyzed"):
            return j
        return None

    assert poll(ready, timeout_s=30.0, interval_s=1.0) is not None
    st = client_inprocess.get(f"/api/v1/imports/{import_id}/status").json()
    assert st["status"] == "ready_to_transform"

    tr = client_inprocess.post(f"/api/v1/imports/{import_id}/transform", json={})
    assert tr.status_code == 200

    def completed():
        s = client_inprocess.get(f"/api/v1/imports/{import_id}/status")
        if s.status_code != 200:
            return None
        if s.json()["status"] == "completed":
            return s.json()
        return None

    assert poll(completed, timeout_s=30.0, interval_s=1.0) is not None
    res = client_inprocess.get(f"/api/v1/imports/{import_id}/result")
    assert res.status_code == 200
    assert res.json()["valid_row_count"] >= 1


def test_malformed_ai_response_falls_back(monkeypatch) -> None:
    import uuid as u

    from app.core.config import Settings
    from app.models.enums import TemplateFieldValueType
    from app.models.template import TemplateField, TemplateVersion
    from app.services.ai.mapping_assist import maybe_enhance_analysis_with_ai
    from app.services.analyzer.template_mapping import TemplateMappingContext

    tv = TemplateVersion(
        id=u.uuid4(),
        template_id=u.uuid4(),
        version=1,
        strict_mode=False,
        auto_accept_confidence=0.9,
        review_threshold=0.7,
        ai_enabled=True,
    )
    f = TemplateField(
        template_version_id=tv.id,
        field_key="email",
        label="Email",
        value_type=TemplateFieldValueType.EMAIL,
        is_builtin=True,
        is_required=False,
        aliases=["mail"],
        allow_empty=True,
        sort_order=0,
    )
    tv.fields = [f]
    ctx = TemplateMappingContext(
        template_version=tv,
        auto_accept_confidence=0.9,
        review_threshold=0.7,
        strict_mode=False,
    )
    analysis = {
        "source_columns": ["mail"],
        "mapping_candidates": [
            {
                "source_column": "mail",
                "target_field": "email",
                "confidence": 0.8,
                "reason": "alias_exact",
                "candidates": [],
            }
        ],
    }

    def boom(*_a, **_k):
        raise ValueError("bad json")

    monkeypatch.setattr("app.services.ai.mapping_assist.call_mapping_assist", boom)
    settings = Settings(ai_mapping_enabled=True, openrouter_api_key="x")
    out, used = maybe_enhance_analysis_with_ai(
        settings,
        analysis,
        template_field_keys=["email"],
        template_fields=[f],
        ctx=ctx,
        ai_enabled_on_template=True,
    )
    assert used is False
    assert out["mapping_candidates"][0]["confidence"] == 0.8
