# Stage 1: Build (optional if you have build steps)
FROM nginx:latest

# Copy static files to Nginx html directory
COPY index.html /usr/share/nginx/html/
COPY static/ /usr/share/nginx/html/static/

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
