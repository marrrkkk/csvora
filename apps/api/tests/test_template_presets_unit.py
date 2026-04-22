from app.services.template_presets import contacts_version_starter


def test_contacts_version_starter_shape() -> None:
    v = contacts_version_starter()
    assert v["validation_rules"]["require_one_of"] == [["email", "phone"]]
    keys = {f["field_key"] for f in v["fields"]}
    assert keys == {"first_name", "last_name", "email", "phone"}
