#!/bin/bash
sleep 5
twurl "/1.1/statuses/lookup.json?id=$(echo $@ | tr ' ' ,)&trim_user=true" | jq -c ".[]|[.id_str, .text]"
