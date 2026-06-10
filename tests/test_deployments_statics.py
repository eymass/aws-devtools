import pytest

from api.deployments_statics import DeploymentStatics


HOST = "my-bucket.s3-website-us-east-1.amazonaws.com"


@pytest.mark.parametrize(
    "raw",
    [
        HOST,
        f"http://{HOST}",
        f"https://{HOST}",
        f"http://{HOST}/",
        f"http://{HOST}/index.html",
        f"http://{HOST}:80",
        f"   http://{HOST}  ",
        f"HTTP://{HOST.upper()}",
    ],
)
def test_normalize_s3_website_domain_strips_to_bare_host(raw):
    assert DeploymentStatics.normalize_s3_website_domain(raw) == HOST


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_normalize_s3_website_domain_rejects_empty(raw):
    with pytest.raises(ValueError):
        DeploymentStatics.normalize_s3_website_domain(raw)


@pytest.mark.parametrize("raw", ["my-bucket", "http://my-bucket", "http://my-bucket/"])
def test_normalize_s3_website_domain_rejects_single_label_hostname(raw):
    with pytest.raises(ValueError, match="single-label hostname"):
        DeploymentStatics.normalize_s3_website_domain(raw)


def test_get_s3_website_origins_uses_bare_host_for_id_and_domain_name():
    origins = DeploymentStatics.get_s3_website_origins(f"http://{HOST}/")
    assert len(origins) == 1
    assert origins[0]["Id"] == HOST
    assert origins[0]["DomainName"] == HOST


def test_default_cache_behavior_target_origin_id_matches_origin_id():
    raw = f"http://{HOST}/"
    origins = DeploymentStatics.get_s3_website_origins(raw)
    behavior = DeploymentStatics.get_s3_optimized_default_cache_behavior(raw)
    assert behavior["TargetOriginId"] == origins[0]["Id"]


def test_normalize_s3_website_domain_strips_fallback_resolved_url_with_lp_key():
    # Mirrors the fallback construction used when no explicit s3_website_url is given:
    #   resolved_url = s3_website_url or (
    #       f"http://{bucket_name}.s3-website-{region}.amazonaws.com/{lp_key}/"
    #   )
    bucket_name = "my-bucket"
    region = "us-east-1"
    lp_key = "Summer-sale"
    resolved_url = (
        f"http://{bucket_name}.s3-website-{region}.amazonaws.com/{lp_key}/"
    )
    assert DeploymentStatics.normalize_s3_website_domain(resolved_url) == HOST
