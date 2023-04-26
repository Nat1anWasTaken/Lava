#!/bin/bash

if ! [ -f ./.cache ]; then
  echo "Go to the following URL: https://accounts.spotify.com/authorize?client_id=$SPOTIFY_CLIENT_ID&response_type=code&redirect_uri=$SPOTIPY_REDIRECT_URI"
  code=$(python ./script/server.py)
  time=$(($(date +%s) + 3600))
  echo $code
  content=$(curl -X POST --user "$SPOTIFY_CLIENT_ID:$SPOTIFY_CLIENT_SECRET" https://accounts.spotify.com/api/token -H 'Content-Type: application/x-www-form-urlencoded' -d "grant_type=authorization_code&code=$code&redirect_uri=$SPOTIPY_REDIRECT_URI" | jq ". += { \"scope\": \"\", \"expires_at\": $time }")
  echo $content > .cache 
  cat .cache
fi

python main.py
