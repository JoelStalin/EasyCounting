FROM odoo:19.0

USER root

RUN pip3 install --no-cache-dir \
    --break-system-packages \
    pycountry>=20.0.0 \
    simplejson \
    debugpy \
    werkzeug>=2.1.0

USER odoo
