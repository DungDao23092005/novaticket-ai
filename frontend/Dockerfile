# ==============================================================
# NovaTicket Frontend — Dockerfile (Multi-stage build)
# ==============================================================

# --------------------------------------------------------------
# Stage 1: Build the React/Vite application
# --------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application for production (outputs to /dist)
RUN npm run build

# --------------------------------------------------------------
# Stage 2: Serve the application using Nginx
# --------------------------------------------------------------
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom nginx configuration for React Router SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
