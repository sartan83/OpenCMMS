#!/usr/bin/env bash
set -euo pipefail

mkdir -p keys
openssl genrsa -out keys/jwt_private.pem 2048
openssl rsa -in keys/jwt_private.pem -pubout -out keys/jwt_public.pem
echo "Generated keys/jwt_private.pem and keys/jwt_public.pem"
