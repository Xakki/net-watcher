FROM nginxinc/nginx-unprivileged:1.28.0-alpine-slim@sha256:c53ed3eda9ef375aa409921676d9eab1f368ada916b970d310410d565a1af2c8

USER root
RUN rm -rf /usr/share/nginx/html \
    && mkdir -p /usr/share/nginx/html \
    && chown 101:101 /usr/share/nginx/html
COPY --chown=101:101 nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 site/index.html /usr/share/nginx/html/index.html
COPY --chown=101:101 site/styles.css /usr/share/nginx/html/styles.css
COPY --chown=101:101 site/audit.md /usr/share/nginx/html/audit.md

USER 101:101
EXPOSE 8080
