# Deployment & Build Configuration

## Overview
This document defines the build processes, deployment strategies, environment configurations, and production optimizations for the candidate research frontend application.

## Build Configuration

### Vite Production Build Setup

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true, // Allow external connections
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },

  // Build optimization
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV !== 'production',
    minify: 'terser',
    target: 'es2020',

    // Chunk splitting strategy
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor libraries
          'vendor-react': ['react', 'react-dom'],
          'vendor-ui': [
            '@radix-ui/react-slot',
            '@radix-ui/react-progress',
            '@radix-ui/react-dialog',
            'class-variance-authority',
            'clsx',
            'tailwind-merge'
          ],
          'vendor-forms': [
            'react-hook-form',
            '@hookform/resolvers',
            'zod'
          ],
          'vendor-api': [
            'axios',
            '@tanstack/react-query'
          ],
          'vendor-state': [
            'zustand'
          ],
          'vendor-utils': [
            'react-dropzone',
            'lucide-react'
          ]
        },

        // Asset naming patterns
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },

    // Terser configuration for production
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      },
      mangle: {
        safari10: true
      }
    }
  },

  // Environment variable handling
  envPrefix: 'VITE_',

  // Preview server (for production build testing)
  preview: {
    port: 3000,
    host: true
  }
})
```

## Environment Configuration

### Environment Variables

```bash
# .env.local (development)
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.doc,.docx,.txt
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=development

# .env.staging
VITE_API_BASE_URL=https://api-staging.candidate-research.com
VITE_WS_BASE_URL=wss://api-staging.candidate-research.com
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.doc,.docx,.txt
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=staging

# .env.production
VITE_API_BASE_URL=https://api.candidate-research.com
VITE_WS_BASE_URL=wss://api.candidate-research.com
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.doc,.docx,.txt
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=production
```

### Environment Type Safety

```typescript
// src/config/env.ts
import { z } from 'zod'

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url(),
  VITE_WS_BASE_URL: z.string().url(),
  VITE_MAX_FILE_SIZE: z.string().transform(Number),
  VITE_ALLOWED_FILE_TYPES: z.string(),
  VITE_APP_VERSION: z.string(),
  VITE_ENVIRONMENT: z.enum(['development', 'staging', 'production'])
})

const validateEnv = () => {
  try {
    return envSchema.parse(import.meta.env)
  } catch (error) {
    console.error('❌ Invalid environment variables:', error)
    throw new Error('Invalid environment configuration')
  }
}

export const env = validateEnv()

// Runtime environment utilities
export const isDevelopment = env.VITE_ENVIRONMENT === 'development'
export const isProduction = env.VITE_ENVIRONMENT === 'production'
export const isStaging = env.VITE_ENVIRONMENT === 'staging'
```

## Docker Configuration

### Multi-stage Dockerfile

```dockerfile
# Dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Development image
FROM base AS dev
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# Build the application
FROM base AS builder
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Build arguments for environment-specific builds
ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL
ARG VITE_ENVIRONMENT=production

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
ENV VITE_ENVIRONMENT=$VITE_ENVIRONMENT

RUN npm run build

# Production image with nginx
FROM nginx:alpine AS production

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy environment template and startup script
COPY env-template.js /usr/share/nginx/html/
COPY docker-entrypoint.sh /

RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
# nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    # Gzip compression
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:;" always;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Handle client-side routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Reverse proxy for API calls
        location /api/ {
            proxy_pass ${API_BASE_URL}/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket proxy
        location /ws/ {
            proxy_pass ${WS_BASE_URL}/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
```

### Runtime Environment Injection

```bash
#!/bin/sh
# docker-entrypoint.sh

# Generate runtime config from environment variables
cat <<EOF > /usr/share/nginx/html/runtime-config.js
window.RUNTIME_CONFIG = {
  API_BASE_URL: '${VITE_API_BASE_URL}',
  WS_BASE_URL: '${VITE_WS_BASE_URL}',
  MAX_FILE_SIZE: ${VITE_MAX_FILE_SIZE:-10485760},
  ENVIRONMENT: '${VITE_ENVIRONMENT:-production}'
};
EOF

# Substitute environment variables in nginx config
envsubst '${API_BASE_URL} ${WS_BASE_URL}' < /etc/nginx/nginx.conf > /tmp/nginx.conf
mv /tmp/nginx.conf /etc/nginx/nginx.conf

# Start nginx
exec "$@"
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/frontend

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run type-check

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm run test

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]
        include:
          - environment: staging
            branch: staging
          - environment: production
            branch: main

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        env:
          VITE_API_BASE_URL: ${{ secrets[format('VITE_API_BASE_URL_{0}', matrix.environment)] }}
          VITE_WS_BASE_URL: ${{ secrets[format('VITE_WS_BASE_URL_{0}', matrix.environment)] }}
          VITE_ENVIRONMENT: ${{ matrix.environment }}
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-${{ matrix.environment }}
          path: dist/

  docker:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push'

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          build-args: |
            VITE_API_BASE_URL=${{ secrets.VITE_API_BASE_URL_PRODUCTION }}
            VITE_WS_BASE_URL=${{ secrets.VITE_WS_BASE_URL_PRODUCTION }}
            VITE_ENVIRONMENT=production

  deploy-staging:
    needs: docker
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    environment: staging

    steps:
      - name: Deploy to staging
        run: |
          echo "Deploy to staging environment"
          # Add deployment commands here

  deploy-production:
    needs: docker
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy to production
        run: |
          echo "Deploy to production environment"
          # Add deployment commands here
```

## Performance Optimization

### Bundle Analysis

```json
// package.json scripts for bundle analysis
{
  "scripts": {
    "analyze": "npm run build && npx vite-bundle-analyzer dist",
    "build:analyze": "cross-env ANALYZE=true vite build",
    "size-limit": "size-limit"
  },
  "size-limit": [
    {
      "path": "dist/assets/index-*.js",
      "limit": "300 KB"
    },
    {
      "path": "dist/assets/vendor-*.js",
      "limit": "500 KB"
    }
  ]
}
```

### Progressive Web App Configuration

```typescript
// vite-plugin-pwa configuration
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'Candidate Research Portal',
        short_name: 'Research Portal',
        description: 'Professional candidate research and evaluation platform',
        theme_color: '#3b82f6',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.candidate-research\.com\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 10,
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    })
  ]
})
```

## Monitoring and Analytics

### Error Tracking Integration

```typescript
// src/utils/error-tracking.ts
import * as Sentry from '@sentry/react'

export const initializeErrorTracking = () => {
  if (isProduction) {
    Sentry.init({
      dsn: process.env.VITE_SENTRY_DSN,
      environment: env.VITE_ENVIRONMENT,
      integrations: [
        new Sentry.BrowserTracing(),
        new Sentry.Replay()
      ],
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0
    })
  }
}

export const ErrorBoundary = Sentry.withErrorBoundary(App, {
  fallback: ({ error, resetError }) => (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Something went wrong</h1>
        <p className="text-muted-foreground mb-4">
          We've been notified about this error and are working to fix it.
        </p>
        <Button onClick={resetError}>Try again</Button>
      </div>
    </div>
  )
})
```

### Performance Monitoring

```typescript
// src/utils/performance.ts
export const trackPerformance = () => {
  // Core Web Vitals
  import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
    getCLS(console.log)
    getFID(console.log)
    getFCP(console.log)
    getLCP(console.log)
    getTTFB(console.log)
  })

  // Custom performance marks
  performance.mark('app-start')

  window.addEventListener('load', () => {
    performance.mark('app-loaded')
    performance.measure('app-load-time', 'app-start', 'app-loaded')
  })
}
```

## Health Checks and Monitoring

### Application Health Check

```typescript
// src/utils/health-check.ts
export const healthCheck = async (): Promise<HealthStatus> => {
  const checks = await Promise.allSettled([
    checkApiConnection(),
    checkLocalStorage(),
    checkWebSocketConnection()
  ])

  return {
    status: checks.every(check => check.status === 'fulfilled') ? 'healthy' : 'unhealthy',
    checks: {
      api: checks[0].status === 'fulfilled',
      localStorage: checks[1].status === 'fulfilled',
      websocket: checks[2].status === 'fulfilled'
    },
    timestamp: new Date().toISOString()
  }
}

const checkApiConnection = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${env.VITE_API_BASE_URL}/health`, {
      method: 'GET',
      timeout: 5000
    })
    return response.ok
  } catch {
    return false
  }
}
```

This comprehensive deployment specification ensures reliable, scalable, and monitored production deployments with proper security, performance optimization, and observability.