FROM nginx:latest

WORKDIR /usr/share/nginx/html

# Copy index.html from frontend folder
COPY index.html .

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
