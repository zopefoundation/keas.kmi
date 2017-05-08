#!/bin/sh
openssl genrsa 1024 > sample.key
openssl req -new -x509 -nodes -sha1 -days 3650 -key sample.key > sample.crt
cat sample.crt sample.key > sample.pem
