# Project Setup Guide

## Overview
This document provides detailed specifications for setting up the React TypeScript frontend project for the candidate deep research application.

## Technology Stack

### Core Framework
- **React 18+** - Latest stable version with concurrent features
- **TypeScript 5+** - Strong typing and modern JavaScript features
- **Vite 5+** - Fast build tool and development server

### Styling & UI
- **Tailwind CSS 3+** - Utility-first CSS framework
- **shadcn/ui** - High-quality component library built on Radix UI
- **Radix UI** - Unstyled, accessible UI primitives
- **clsx** - Conditional CSS class utility
- **tailwind-merge** - Tailwind CSS class merging utility

### Form Handling & Validation
- **react-hook-form 7+** - Performant forms with minimal re-renders
- **zod 3+** - TypeScript-first schema validation
- **@hookform/resolvers** - Validation library resolvers for react-hook-form

### File Upload
- **react-dropzone 14+** - File drag & drop functionality
- **@types/file-saver** - File download utilities (for results export)

### HTTP Client & State
- **axios 1+** - Promise-based HTTP client
- **react-query/tanstack-query 5+** - Server state management
- **zustand 4+** - Lightweight client state management

### Development Tools
- **ESLint 8+** - JavaScript/TypeScript linting
- **Prettier 3+** - Code formatting
- **@typescript-eslint/parser** - TypeScript ESLint parser
- **@typescript-eslint/eslint-plugin** - TypeScript ESLint rules

## Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── index.html
├── src/
│   ├── components/
│   │   ├── ui/                 # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── progress.tsx
│   │   │   └── index.ts
│   │   ├── forms/              # Form-specific components
│   │   │   ├── linkedin-url-input.tsx
│   │   │   ├── cv-upload.tsx
│   │   │   ├── job-description-input.tsx
│   │   │   └── index.ts
│   │   ├── processing/         # Processing flow components
│   │   │   ├── loading-screen.tsx
│   │   │   ├── progress-indicator.tsx
│   │   │   ├── status-message.tsx
│   │   │   └── index.ts
│   │   ├── results/            # Results display components
│   │   │   ├── results-dashboard.tsx
│   │   │   ├── candidate-profile.tsx
│   │   │   ├── match-analysis.tsx
│   │   │   └── index.ts
│   │   └── layout/             # Layout components
│   │       ├── header.tsx
│   │       ├── footer.tsx
│   │       └── index.ts
│   ├── hooks/                  # Custom React hooks
│   │   ├── use-file-upload.ts
│   │   ├── use-research.ts
│   │   ├── use-debounce.ts
│   │   └── index.ts
│   ├── services/               # API and external services
│   │   ├── api.ts
│   │   ├── validation.ts
│   │   ├── file-utils.ts
│   │   └── index.ts
│   ├── types/                  # TypeScript type definitions
│   │   ├── api.ts
│   │   ├── research.ts
│   │   ├── forms.ts
│   │   └── index.ts
│   ├── store/                  # State management
│   │   ├── research-store.ts
│   │   ├── ui-store.ts
│   │   └── index.ts
│   ├── utils/                  # Utility functions
│   │   ├── cn.ts              # clsx + tailwind-merge utility
│   │   ├── constants.ts
│   │   ├── format.ts
│   │   └── index.ts
│   ├── pages/                  # Page components
│   │   ├── home.tsx
│   │   ├── research.tsx
│   │   └── index.ts
│   ├── App.tsx                 # Main application component
│   ├── main.tsx               # Application entry point
│   ├── index.css              # Global styles and Tailwind imports
│   └── vite-env.d.ts          # Vite type definitions
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.js
├── components.json             # shadcn/ui configuration
├── .eslintrc.cjs
├── .prettierrc
├── .gitignore
└── README.md
```

## Configuration Files

### package.json Dependencies
```json
{
  "name": "candidate-research-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx}\"",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.48.2",
    "react-dropzone": "^14.2.3",
    "@hookform/resolvers": "^3.3.2",
    "zod": "^3.22.4",
    "axios": "^1.6.2",
    "@tanstack/react-query": "^5.8.4",
    "zustand": "^4.4.7",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-progress": "^1.0.3",
    "@radix-ui/react-dialog": "^1.0.5",
    "class-variance-authority": "^0.7.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react-swc": "^3.5.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "prettier": "^3.1.1",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
```

### TypeScript Configuration (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### Vite Configuration (vite.config.ts)
```typescript
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
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-slot', '@radix-ui/react-progress'],
          forms: ['react-hook-form', '@hookform/resolvers', 'zod'],
          api: ['axios', '@tanstack/react-query']
        }
      }
    }
  }
})
```

### Tailwind Configuration (tailwind.config.js)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### ESLint Configuration (.eslintrc.cjs)
```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'prefer-const': 'error',
    'no-var': 'error',
  },
}
```

## Setup Commands

### 1. Create Project
```bash
cd frontend/
npm create vite@latest . -- --template react-ts
```

### 2. Install Dependencies
```bash
npm install react react-dom
npm install -D @types/react @types/react-dom

# Form handling
npm install react-hook-form @hookform/resolvers zod

# File upload
npm install react-dropzone

# HTTP client and state
npm install axios @tanstack/react-query zustand

# UI components
npm install @radix-ui/react-slot @radix-ui/react-progress @radix-ui/react-dialog
npm install class-variance-authority clsx tailwind-merge lucide-react

# Styling
npm install -D tailwindcss postcss autoprefixer
npm install -D tailwindcss-animate

# Development tools
npm install -D @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install -D eslint-plugin-react-hooks eslint-plugin-react-refresh
npm install -D prettier
```

### 3. Initialize Configurations
```bash
# Initialize Tailwind
npx tailwindcss init -p

# Initialize shadcn/ui
npx shadcn-ui@latest init
```

## Environment Setup

### Development Environment
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **VS Code**: Recommended with extensions:
  - TypeScript and JavaScript Language Features
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
  - Auto Rename Tag

### Environment Variables (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_MAX_FILE_SIZE=10485760  # 10MB in bytes
VITE_ALLOWED_FILE_TYPES=.pdf,.doc,.docx
```

## Quality Standards

### Code Style
- **TypeScript strict mode** enabled
- **Prettier** for consistent formatting
- **ESLint** for code quality
- **Absolute imports** using `@/` alias

### Component Standards
- Functional components with TypeScript
- Props interfaces explicitly defined
- Default exports for pages, named exports for components
- Consistent file naming (kebab-case)

### Testing Setup (Future)
- **Vitest** for unit testing
- **React Testing Library** for component testing
- **Playwright** for E2E testing

## Performance Considerations

### Bundle Optimization
- Code splitting by feature
- Lazy loading for routes
- Tree shaking enabled
- Asset optimization

### Development Experience
- Hot Module Replacement (HMR)
- Fast refresh for React components
- TypeScript type checking
- Source maps for debugging

## Security Considerations

### File Upload Security
- File type validation
- File size limits
- Client-side virus scanning (future)
- Secure file storage

### API Security
- CORS configuration
- Request/response validation
- Error handling without information leakage
- HTTPS enforcement in production

## Next Steps

After project setup:
1. Initialize shadcn/ui components (Button, Input, Card, Progress)
2. Set up base utility functions (cn, constants)
3. Configure API client with axios
4. Implement basic routing structure
5. Set up global state management

This setup provides a robust foundation for building a professional, scalable React TypeScript application that integrates seamlessly with the Coral Protocol backend.