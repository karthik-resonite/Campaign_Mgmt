FROM node:20-alpine
WORKDIR /usr/src/app
# Install deps first to leverage layer caching
COPY package*.json ./
RUN npm install
# Copy the rest (for dev we also mount it, but this helps in CI)
COPY . .
EXPOSE 443