def test_adaptive_learning_slow_path(client):
    response = client.post(
        "/learn",
        params={
            "user_id": "test_user",
            "concept": "fractions",
            "answer_correct": False,
            "time_taken_sec": 45
        },
        headers={"Accept-Language": "en"}
    )

    assert response.status_code == 200
    data = response.json()

    # Learning adaptation
    assert data["learning_state"]["difficulty"] == "easy"
    assert data["learning_state"]["pace"] == "slow"
    assert data["next_step_type"] == "explanation"
    assert data["adaptation_reason"] == "low_accuracy_or_slow_pace"

    # Accessibility
    assert data["accessibility"]["language"] == "en"

    # Cloud Run runtime visibility
    assert data["runtime"]["platform"] == "google-cloud-run"
    assert "service" in data["runtime"]
    assert "region" in data["runtime"]


def test_adaptive_learning_fast_path(client):
    response = client.post(
        "/learn",
        params={
            "user_id": "test_user",
            "concept": "fractions",
            "answer_correct": True,
            "time_taken_sec": 5
        },
        headers={"Accept-Language": "en"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["learning_state"]["difficulty"] == "hard"
    assert data["learning_state"]["pace"] == "fast"
    assert data["next_step_type"] == "challenge"


def test_learning_invalid_input(client):
    response = client.post(
        "/learn",
        params={
            "user_id": "",
            "concept": "",
            "answer_correct": True,
            "time_taken_sec": -1
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "INVALID_INPUT"