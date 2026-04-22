
1. create another api like deploy_environment(), deploy_static() which will deploy cloudfront on domain not a eb environment but in the origin,
but an s3 website bucket url, which cache policy optimized.
2. create an example call to this new API
3. make sure to reuse all classes and modules, extend if needed, add proper logging.
4. This API will respond with jobId, since its execution is a background job that can be polled, reuse existing.
