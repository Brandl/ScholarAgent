from scholaragent._endpoints import DEFAULT_FIELDS, ENDPOINTS, ENDPOINTS_BY_NAME


def test_no_duplicate_fields():
    """Regression: citation/reference fields previously had 'title' duplicated."""
    for key, fields_str in DEFAULT_FIELDS.items():
        fields = fields_str.split(",")
        assert len(fields) == len(set(fields)), f"Duplicate field in {key}: {fields}"


def test_all_endpoints_have_unique_names():
    names = [ep.name for ep in ENDPOINTS]
    assert len(names) == len(set(names))


def test_endpoints_by_name_matches():
    assert len(ENDPOINTS_BY_NAME) == len(ENDPOINTS)
    for ep in ENDPOINTS:
        assert ENDPOINTS_BY_NAME[ep.name] is ep
