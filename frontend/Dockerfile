FROM node:20-slim

WORKDIR /app

# Install system dependencies if needed (none for basic node)
# RUN apt-get update && apt-get install -y --no-install-recommends ...

COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose Vite's default dev port
EXPOSE 5173

# Run Vite dev server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
