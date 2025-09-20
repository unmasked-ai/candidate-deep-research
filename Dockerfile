# syntax=docker/dockerfile:1
FROM eclipse-temurin:21-jdk AS build

# Optional tools if we need to fetch the upstream coral-server when missing
RUN apt-get update && apt-get install -y git bash && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .

# Ensure coral-server exists even if submodules aren't fetched
RUN test -f coral-server/gradlew || (rm -rf coral-server && git clone --depth 1 https://github.com/Coral-Protocol/coral-server.git coral-server)

WORKDIR /build/coral-server
# Build an uber JAR at image build time (faster startup on Fly)
RUN ./gradlew --no-daemon build -x test

FROM eclipse-temurin:21-jre
WORKDIR /app

# Copy registry (if present in repo root)
COPY --from=build /build/registry.toml /app/registry.toml

# Copy built artifacts and select the fat JAR
COPY --from=build /build/coral-server/build/libs/ /app/
RUN ln -s "$(ls -1 /app/coral-server-*.jar | grep -v '\-plain\.jar' | head -n 1)" /app/app.jar

# Environment for platform hints and runtime config
ENV PORT=5555
ENV REGISTRY_FILE_PATH=/app/registry.toml

EXPOSE 5555

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
