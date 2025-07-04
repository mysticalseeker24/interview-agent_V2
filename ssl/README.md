# SSL Certificates Directory

This directory is for SSL certificates when running NGINX with HTTPS.

## Development Setup
For development, you can generate self-signed certificates:

```bash
# Generate a self-signed certificate (for development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/nginx-selfsigned.key \
    -out ssl/nginx-selfsigned.crt

# Generate a strong Diffie-Hellman group
openssl dhparam -out ssl/dhparam.pem 2048
```

## Production Setup
For production, use certificates from a trusted Certificate Authority (CA) like:
- Let's Encrypt (free)
- DigiCert
- GoDaddy
- etc.

Place your production certificates in this directory:
- `ssl/cert.crt` - Your SSL certificate
- `ssl/private.key` - Your private key
- `ssl/ca-bundle.crt` - CA bundle (if required)
