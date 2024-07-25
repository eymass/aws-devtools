#bin/bash

# This script will remove expired certificates from the AWS Certificate Manager
# Usage: ./clear_expired_certificates.sh

aws acm list-certificates --certificate-statuses "EXPIRED" "FAILED" "REVOKED" "INACTIVE" > certificates.json
jq -r ".CertificateSummaryList[] | .CertificateArn" certificates.json > tmp.json

while read -r certificate_arn; do
  echo "checking $certificate_arn #"
  if [ -z "$certificate_arn" ]; then
    echo "Certificate $certificate_arn not found"
    continue
  fi
  echo "deleting certificate $certificate_arn"
  aws acm delete-certificate --certificate-arn $certificate_arn
done < tmp.json


