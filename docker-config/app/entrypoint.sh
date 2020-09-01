echo "${SSL_CERTIFICATE}" | base64 -d > /usr/src/app/certificate.crt && \
echo "${SSL_CERTIFICATE_PRIVATE_KEY}" | base64 -d > /usr/src/app/private_key.key && \

python manage.py migrate && \
uwsgi --ini uwsgi.ini
