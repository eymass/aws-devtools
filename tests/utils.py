import json
from app import BUCKETS_ROUTE


def create_bucket_tests(app, name: str) -> dict:
    return app.test_client().post(BUCKETS_ROUTE,
                                  data=json.dumps({
                                      "name": name,
                                  }),
                                  content_type='application/json')
