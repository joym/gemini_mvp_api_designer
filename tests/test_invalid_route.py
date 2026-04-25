def test_invalid_route_returns_404(client):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404