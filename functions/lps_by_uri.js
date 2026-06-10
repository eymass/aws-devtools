function handler(event) {
  var request = event.request;
  var headers = request.headers;
  var uri = request.uri;
  var query = request.querystring || '';

  var hasTtclid = false;
  if (typeof query === 'string') {
    hasTtclid = query.indexOf('ttclid=') !== -1;
  } else if (typeof query === 'object' && query !== null) {
    hasTtclid = Object.prototype.hasOwnProperty.call(query, 'ttclid');
  }

  var ua = headers['user-agent'] && headers['user-agent'].value
    ? headers['user-agent'].value.toLowerCase()
    : '';
  var country = headers['cloudfront-viewer-country'] && headers['cloudfront-viewer-country'].value
    ? headers['cloudfront-viewer-country'].value.toUpperCase()
    : '??';

  var botKeywords = ['bot', 'crawl', 'spider', 'headless', 'python', 'curl', 'wget'];
  var isBot = botKeywords.some(function (k) { return ua.indexOf(k) !== -1; });
  var isTikTokIAB = ua.indexOf('tiktok') !== -1 || ua.indexOf('bytedance') !== -1;

  var whitelistCountries = ['SA', 'IL', 'DE', 'FR', 'NL'];
  var countryAllowed = whitelistCountries.indexOf(country) !== -1;

  var blacklisted = isBot || isTikTokIAB || !countryAllowed || !hasTtclid;

  if (blacklisted) {
    request.uri = '/index.html';
    return request;
  }

  if (uri === '' || uri === '/') {
    request.uri = '/index.html';
    return request;
  }

  var lastSegment = uri.substring(uri.lastIndexOf('/') + 1);
  if (lastSegment.indexOf('.') === -1) {
    var trimmed = uri.charAt(uri.length - 1) === '/' ? uri.substring(0, uri.length - 1) : uri;
    request.uri = trimmed + '/index.html';
  }

  return request;
}