#bin/bash
hosted_zones_ids=$1
# example: Z1Z1Z1Z1Z1Z1Z1,Z2Z2Z2Z2Z2Z2
hosted_zones_ids=(${hosted_zones_ids//,/ })

echo "cleaning up hosted zones: $hosted_zones_ids"

for zone_id in "${hosted_zones_ids[@]}"; do
  if [ -z "$zone_id" ]; then
    echo "Hosted zone $zone_id not found"
    continue
  fi
  echo "listing hosted zone $zone_id records"
  aws route53 list-resource-record-sets --hosted-zone-id $zone_id > records.json
  echo "deleting hosted zone records"
  
  jq -c ".ResourceRecordSets[]" records.json > tmp.json
  while read -r line; do
    echo "deleting record $line"
    record_name=$(echo $line | jq -r ".Name")
    record_type=$(echo $line | jq -r ".Type")
    if [ -z "$record_name" ]; then
      echo "record name is empty"
      continue
    fi
    if [ "$record_type" == "NS" ] || [ "$record_type" == "SOA" ]; then
      echo "record type is NS or SOA"
      continue
    fi
    echo "calling change-resource-record-sets on $line"
    aws route53 change-resource-record-sets --hosted-zone-id $zone_id --change-batch "{
      \"Changes\": [
        {
          \"Action\": \"DELETE\",
          \"ResourceRecordSet\": $line
        }
      ]
    }"
  done < tmp.json
  
  echo "deleting hosted zone $zone_id"
  aws route53 delete-hosted-zone --id $zone_id
  # rm records.json
done


