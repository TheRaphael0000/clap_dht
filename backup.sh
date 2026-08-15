#!/bin/zsh
cd -- "$(dirname -- "$0")"
docker compose stop
borg create $BORG_REPO::{now} data
docker compose start
