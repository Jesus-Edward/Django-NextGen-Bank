FROM docker.io/nginx:1.27.0-alpine3.19-slim

# remove the default nginx conf that comes with the above image
RUN rm /etc/nginx/conf.d/default.conf

# Replace the default conf file with the one we created
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

