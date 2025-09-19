# syntax=docker/dockerfile:1
FROM eclipse-temurin:21-jdk

# Needed if we decide to fetch submodules or tools during build
RUN apt-get update && apt-get install -y git bash && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Bring in your fork (including registry.toml at repo root)
COPY . .

# Ensure coral-server code exists even if submodules aren't auto-fetched by the platform
# (Render may not clone with --recurse-submodules)
RUN test -f coral-server/gradlew || (rm -rf coral-server && git clone --depth 1 https://github.com/Coral-Protocol/coral-server.git coral-server)

# Pre-warm Gradle to speed boots
WORKDIR /app/coral-server
RUN ./gradlew --no-daemon --version && ./gradlew --no-daemon classes

# Helpful for Render's port detection (server defaults to 5555)
ENV PORT=5555
ENV REGISTRY_FILE_PATH=/app/registry.toml

# For documentation only; Render autodetects listening ports for Docker images
EXPOSE 5555

# Start Coral Server via gradle-run, pointing at your registry.toml
CMD ["bash", "-lc", "REGISTRY_FILE_PATH=$REGISTRY_FILE_PATH ./gradlew --no-daemon run"]
