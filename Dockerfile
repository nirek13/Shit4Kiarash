# syntax = docker/dockerfile:1

# ===== Base stage =====
ARG NODE_VERSION=20.18.0
FROM node:${NODE_VERSION}-slim AS base

LABEL fly_launch_runtime="Node.js"

WORKDIR /app
ENV NODE_ENV=production

# Install Python
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y python3 python3-pip build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ===== Build stage =====
FROM base AS build

# Install Node modules
COPY package*.json ./
RUN npm ci

# Copy app code
COPY . .

# ===== Final stage =====
FROM base

# Copy built app
COPY --from=build /app /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 3000

# Start the server
CMD ["npm", "run", "start"]
