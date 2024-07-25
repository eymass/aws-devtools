#bin/bash
certificates_domains=$1

echo "cleaning up certificates: $certificates_domains"

for domain in "${certificates_domains[@]}"; do
  if [ -z "$domain" ]; then
    echo "Certificate $domain not found"
    continue
  fi
  echo "listing certificate $domain"
  certificate_arn=$(aws acm list-certificates --certificate-statuses "EXPIRED" "FAILED" "REVOKED" "INACTIVE" | jq -r ".CertificateSummaryList[] | select(.DomainName == \"$domain\") | .CertificateArn")
  if [ -z "$certificate_arn" ]; then
    echo "Certificate $domain not found"
    continue
  fi
  echo "deleting certificate $certificate_arn $domain"
  aws acm delete-certificate --certificate-arn $certificate_arn
done

