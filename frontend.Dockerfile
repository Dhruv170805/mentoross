# Frontend Dockerfile (Standalone HTML Version)
FROM nginx:alpine

# Copy the standalone HTML app to the default nginx directory
COPY mentoross-app.html /usr/share/nginx/html/index.html

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
