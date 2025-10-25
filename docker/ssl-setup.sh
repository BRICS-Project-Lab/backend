#!/bin/bash

set -e

if [ -z "$DOMAIN_NAME" ]; then
    echo "No domain name specified. Skipping SSL setup."
    exit 0
fi

echo "Setting up SSL for domain: $DOMAIN_NAME"

sed -i "s/your-domain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/default

mkdir -p /var/www/certbot

certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@$DOMAIN_NAME \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN_NAME

nginx -s reload

echo "SSL setup completed for $DOMAIN_NAME"