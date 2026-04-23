import json

ROUTING_TYPES = ('geo', 'ab', 'utm', 'ip', 'device', 'path', 'composite')


def _geo(config: dict) -> str:
    country_map = config.get(
        'country_to_variant',
        {'IL': 'il', 'DE': 'de', 'AT': 'de', 'CH': 'de'},
    )
    map_js = json.dumps(country_map)
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        "  if (req.uri !== '/' && req.uri !== '/index.html') return req;\n"
        "  var h = req.headers['cloudfront-viewer-country'];\n"
        "  var code = h ? h.value : 'US';\n"
        f"  var variants = {map_js};\n"
        "  var variant = variants[code] || 'default';\n"
        "  req.uri = '/variants/' + variant + '/index.html';\n"
        "  return req;\n"
        "}"
    )


def _ab(_config: dict) -> str:
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        "  if (req.uri !== '/' && req.uri !== '/index.html') return req;\n"
        "  var cookies = req.cookies || {};\n"
        "  var bucket = cookies['ab_bucket'] && cookies['ab_bucket'].value;\n"
        "  if (bucket !== 'a' && bucket !== 'b') {\n"
        "    var seed = (req.headers['user-agent'] ? req.headers['user-agent'].value : '') +\n"
        "               (event.viewer && event.viewer.ip ? event.viewer.ip : '');\n"
        "    var hash = 0;\n"
        "    for (var i = 0; i < seed.length; i++) hash = ((hash << 5) - hash + seed.charCodeAt(i)) | 0;\n"
        "    bucket = (Math.abs(hash) % 2 === 0) ? 'a' : 'b';\n"
        "  }\n"
        "  req.uri = '/variants/' + bucket + '/index.html';\n"
        "  req.headers['x-ab-bucket'] = { value: bucket };\n"
        "  return req;\n"
        "}"
    )


def _utm(config: dict) -> str:
    campaign_map = config.get(
        'campaign_to_variant',
        {'spring25': 'spring25', 'blackfriday': 'bf2025', 'webinar': 'webinar-q1'},
    )
    map_js = json.dumps(campaign_map)
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        "  if (req.uri !== '/' && req.uri !== '/index.html') return req;\n"
        "  var qs = req.querystring || {};\n"
        "  var campaign = qs.campaign && qs.campaign.value;\n"
        f"  var allowed = {map_js};\n"
        "  var variant = (campaign && allowed[campaign]) || 'default';\n"
        "  req.uri = '/variants/' + variant + '/index.html';\n"
        "  return req;\n"
        "}"
    )


def _ip(config: dict) -> str:
    internal = json.dumps(config.get('internal_prefixes', ['203.0.113.', '198.51.100.']))
    partner = json.dumps(config.get('partner_prefixes', ['192.0.2.']))
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        "  if (req.uri !== '/' && req.uri !== '/index.html') return req;\n"
        "  var ip = event.viewer && event.viewer.ip;\n"
        "  if (!ip) return req;\n"
        f"  var internal = {internal};\n"
        f"  var partner = {partner};\n"
        "  var variant = 'default';\n"
        "  for (var i = 0; i < internal.length; i++) {\n"
        "    if (ip.indexOf(internal[i]) === 0) { variant = 'internal'; break; }\n"
        "  }\n"
        "  if (variant === 'default') {\n"
        "    for (var j = 0; j < partner.length; j++) {\n"
        "      if (ip.indexOf(partner[j]) === 0) { variant = 'partner'; break; }\n"
        "    }\n"
        "  }\n"
        "  req.headers['x-variant-bucket'] = { value: variant };\n"
        "  req.uri = '/variants/' + variant + '/index.html';\n"
        "  return req;\n"
        "}"
    )


def _device(_config: dict) -> str:
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        "  if (req.uri !== '/' && req.uri !== '/index.html') return req;\n"
        "  var isMobile = req.headers['cloudfront-is-mobile-viewer'];\n"
        "  var isTablet = req.headers['cloudfront-is-tablet-viewer'];\n"
        "  var variant = 'desktop';\n"
        "  if ((isMobile && isMobile.value === 'true') || (isTablet && isTablet.value === 'true')) {\n"
        "    variant = 'mobile';\n"
        "  }\n"
        "  req.uri = '/variants/' + variant + '/index.html';\n"
        "  return req;\n"
        "}"
    )


def _path(config: dict) -> str:
    prefix = json.dumps(config.get('prefix', '/promo'))
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        f"  var prefix = {prefix};\n"
        "  var escaped = prefix.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');\n"
        "  req.uri = req.uri.replace(new RegExp('^' + escaped), '') || '/';\n"
        "  if (req.uri.slice(-1) === '/') req.uri += 'index.html';\n"
        "  return req;\n"
        "}"
    )


def _composite(config: dict) -> str:
    country = json.dumps(config.get('country', 'IL'))
    locale = json.dumps(config.get('locale', 'il'))
    return (
        "function handler(event) {\n"
        "  var req = event.request;\n"
        "  if (req.uri !== '/' && req.uri !== '/index.html') return req;\n"
        "  var h = req.headers['cloudfront-viewer-country'];\n"
        "  var code = h ? h.value : 'US';\n"
        f"  if (code !== {country}) {{\n"
        "    req.uri = '/variants/default/index.html';\n"
        "    req.headers['x-variant-bucket'] = { value: 'default' };\n"
        "    return req;\n"
        "  }\n"
        "  var cookies = req.cookies || {};\n"
        "  var bucket = cookies['ab_bucket'] && cookies['ab_bucket'].value;\n"
        "  if (bucket !== 'a' && bucket !== 'b') {\n"
        "    var ip = (event.viewer && event.viewer.ip) || '';\n"
        "    var ua = (req.headers['user-agent'] && req.headers['user-agent'].value) || '';\n"
        "    var seed = ip + ua;\n"
        "    var hv = 0;\n"
        "    for (var i = 0; i < seed.length; i++) hv = ((hv << 5) - hv + seed.charCodeAt(i)) | 0;\n"
        "    bucket = (Math.abs(hv) % 2 === 0) ? 'a' : 'b';\n"
        "  }\n"
        f"  var locale = {locale};\n"
        "  req.uri = '/variants/' + locale + '-' + bucket + '/index.html';\n"
        "  req.headers['x-variant-bucket'] = { value: locale + '-' + bucket };\n"
        "  return req;\n"
        "}"
    )


_BUILDERS = {
    'geo': _geo,
    'ab': _ab,
    'utm': _utm,
    'ip': _ip,
    'device': _device,
    'path': _path,
    'composite': _composite,
}


def build_function_code(routing_type: str, routing_config: dict | None = None) -> str:
    """Return CloudFront Function JS for routing_type, interpolating routing_config values."""
    if routing_type not in _BUILDERS:
        raise ValueError(
            f"Unknown routing_type '{routing_type}'. Valid types: {list(_BUILDERS)}"
        )
    return _BUILDERS[routing_type](routing_config or {})
