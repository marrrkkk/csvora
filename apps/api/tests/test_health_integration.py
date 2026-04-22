def test_live_health_endpoint(client_inprocess) -> None:
    response = client_inprocess.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_health_ready_endpoint(client_inprocess) -> None:
    response = client_inprocess.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"
    assert body["checks"]["storage"] == "ok"


def test_metrics_endpoint_exposes_http_metric(client_inprocess) -> None:
    client_inprocess.get("/health/live")
    response = client_inprocess.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text

