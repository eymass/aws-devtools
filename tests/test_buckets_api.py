import json
from app import BUCKETS_ROUTE


def test_create_bucket_expect_success(app):
    user_data = {
        "name": "platform2011-europas-test3",
    }
    response = app.test_client().post(BUCKETS_ROUTE,
                           data=json.dumps(user_data),
                           content_type='application/json')
    assert response.status_code == 201
    assert 'errors' not in response.json

    response = app.test_client().DELETE(BUCKETS_ROUTE,
                           data=json.dumps(user_data),
                           content_type='application/json')
    assert response.status_code == 204
    assert 'errors' not in response.json
