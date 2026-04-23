from unittest.mock import MagicMock

from cleaner import DeploymentCleaner


def _make_cleaner(cf=None, fn=None, cert=None, r53=None):
    cleaner = DeploymentCleaner.__new__(DeploymentCleaner)
    cleaner.cf_manager = cf or MagicMock()
    cleaner.cf_fn_manager = fn or MagicMock()
    cleaner.cert_manager = cert or MagicMock()
    cleaner.route53_manager = r53 or MagicMock()
    return cleaner


def test_clean_static_deployment_calls_all_resources():
    cleaner = _make_cleaner()
    results = cleaner.clean_static_deployment('example.com', 'example-com-viewer-request')

    cleaner.cf_manager.remove_distribution_by_domain.assert_called_once_with('example.com')
    cleaner.cf_fn_manager.delete_function.assert_called_once_with('example-com-viewer-request')
    cleaner.cert_manager.remove_certificate_by_domain.assert_called_once_with('example.com')
    cleaner.route53_manager.remove_hosted_zone_by_domain.assert_called_once_with('example.com')

    assert results['cloudfront_distribution'] == 'removed'
    assert results['viewer_request_function'] == 'removed'
    assert results['acm_certificate'] == 'removed'
    assert results['route53_hosted_zone'] == 'removed'


def test_clean_static_deployment_skips_function_when_name_not_given():
    cleaner = _make_cleaner()
    results = cleaner.clean_static_deployment('example.com')

    cleaner.cf_fn_manager.delete_function.assert_not_called()
    assert 'viewer_request_function' not in results


def test_clean_static_deployment_records_errors():
    cf = MagicMock()
    cf.remove_distribution_by_domain.side_effect = RuntimeError("timeout")
    cleaner = _make_cleaner(cf=cf)

    results = cleaner.clean_static_deployment('bad.example.com')

    assert 'error:' in results['cloudfront_distribution']
    # other resources still attempted
    cleaner.cert_manager.remove_certificate_by_domain.assert_called_once()
    cleaner.route53_manager.remove_hosted_zone_by_domain.assert_called_once()


def test_clean_continues_after_partial_failure():
    cert = MagicMock()
    cert.remove_certificate_by_domain.side_effect = RuntimeError("no cert found")
    cleaner = _make_cleaner(cert=cert)

    results = cleaner.clean_static_deployment('example.com')

    assert 'error:' in results['acm_certificate']
    assert results['route53_hosted_zone'] == 'removed'
