#!/bin/bash
cat ./../all_data/uniformly_sampled.tsv | cut -f2 | xargs -n100 ./fetch.sh > ./../all_data/original_tweets.json
