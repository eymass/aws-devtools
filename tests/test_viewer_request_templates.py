import pytest
from viewer_request_templates import build_function_code, ROUTING_TYPES


@pytest.mark.parametrize("routing_type", ROUTING_TYPES)
def test_build_function_code_returns_string(routing_type):
    code = build_function_code(routing_type)
    assert isinstance(code, str)
    assert 'function handler(event)' in code
    assert 'return req' in code


def test_geo_embeds_country_map():
    code = build_function_code('geo', {'country_to_variant': {'US': 'us', 'IL': 'il'}})
    assert '"US"' in code or "'US'" in code
    assert 'variants' in code


def test_utm_embeds_campaign_map():
    code = build_function_code('utm', {'campaign_to_variant': {'summer': 'summer25'}})
    assert 'summer' in code
    assert 'allowed' in code


def test_ip_embeds_prefixes():
    code = build_function_code('ip', {
        'internal_prefixes': ['10.0.0.'],
        'partner_prefixes': ['172.16.'],
    })
    assert '10.0.0.' in code
    assert '172.16.' in code


def test_path_embeds_prefix():
    code = build_function_code('path', {'prefix': '/campaign'})
    assert '/campaign' in code


def test_composite_embeds_country_and_locale():
    code = build_function_code('composite', {'country': 'DE', 'locale': 'de'})
    assert '"DE"' in code or "'DE'" in code


def test_unknown_routing_type_raises():
    with pytest.raises(ValueError, match="Unknown routing_type"):
        build_function_code('nonexistent')


def test_default_config_produces_valid_code():
    for rt in ROUTING_TYPES:
        code = build_function_code(rt)
        assert len(code) > 0


def test_geo_default_config_has_il_variant():
    code = build_function_code('geo')
    assert 'IL' in code


def test_ab_code_has_hash_logic():
    code = build_function_code('ab')
    assert 'hash' in code
    assert 'ab_bucket' in code
