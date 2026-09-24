# ---------- Build Stage ----------
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --silent
COPY . .
RUN npm run build

# ---------- Minimal output ----------
FROM alpine:3.18
WORKDIR /app
COPY --from=build /app/build /build
CMD ["sh", "-c", "echo 'React build ready at /build'"]
