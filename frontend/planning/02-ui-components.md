# UI Components Specification

## Overview
This document defines the base UI components that will be built using shadcn/ui and Radix UI primitives. These components provide the foundation for all interface elements in the application.

## Component Architecture

### Base Component Principles
- Built on Radix UI primitives for accessibility
- Styled with Tailwind CSS using consistent design tokens
- TypeScript interfaces for all props
- Variant-based styling using class-variance-authority
- Consistent naming conventions (kebab-case files, PascalCase components)

### Design System Tokens

#### Colors
```typescript
// Primary colors for main actions and branding
primary: "hsl(var(--primary))"           // Blue-600
primary-foreground: "hsl(var(--primary-foreground))"  // White

// Secondary colors for supporting elements
secondary: "hsl(var(--secondary))"       // Gray-100
secondary-foreground: "hsl(var(--secondary-foreground))" // Gray-900

// Background and surface colors
background: "hsl(var(--background))"     // White
card: "hsl(var(--card))"                 // White with subtle border
muted: "hsl(var(--muted))"               // Gray-50

// Interactive elements
input: "hsl(var(--input))"               // Border color for inputs
ring: "hsl(var(--ring))"                 // Focus ring color
border: "hsl(var(--border))"             // General border color

// Feedback colors
destructive: "hsl(var(--destructive))"   // Red-500 for errors
```

#### Typography Scale
```typescript
// Font sizes following design system
text-xs: "0.75rem"    // 12px
text-sm: "0.875rem"   // 14px
text-base: "1rem"     // 16px
text-lg: "1.125rem"   // 18px
text-xl: "1.25rem"    // 20px
text-2xl: "1.5rem"    // 24px
text-3xl: "1.875rem"  // 30px
```

#### Spacing Scale
```typescript
// Consistent spacing using Tailwind's scale
spacing: "0.25rem"    // 4px increments
padding: "0.5rem"     // 8px standard
margin: "1rem"        // 16px standard
gap: "1.5rem"         // 24px for layouts
```

## Core Components

### 1. Button Component

**File**: `src/components/ui/button.tsx`

```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  asChild?: boolean
}
```

**Variants**:
- `default`: Primary blue background, white text
- `destructive`: Red background for dangerous actions
- `outline`: Transparent background, colored border
- `secondary`: Gray background for secondary actions
- `ghost`: Transparent background, hover state only
- `link`: Text styling with underline

**Sizes**:
- `sm`: 32px height, small padding
- `default`: 40px height, standard padding
- `lg`: 48px height, large padding
- `icon`: Square button for icons only

**Usage Examples**:
```typescript
<Button>Start Research</Button>
<Button variant="outline" size="sm">Cancel</Button>
<Button variant="destructive">Delete</Button>
```

### 2. Input Component

**File**: `src/components/ui/input.tsx`

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  icon?: React.ReactNode
}
```

**Features**:
- Error state styling with red border
- Optional icon support (prefix or suffix)
- Focus states with ring styling
- Disabled state with muted appearance
- Consistent height and padding

**Usage Examples**:
```typescript
<Input placeholder="Enter LinkedIn URL" />
<Input error={true} placeholder="Invalid URL" />
<Input icon={<LinkIcon />} placeholder="LinkedIn Profile" />
```

### 3. Card Component

**File**: `src/components/ui/card.tsx`

```typescript
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated'
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}
interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}
interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}
```

**Subcomponents**:
- `CardHeader`: Title and description area
- `CardContent`: Main content area with padding
- `CardFooter`: Actions area at bottom

**Usage Examples**:
```typescript
<Card>
  <CardHeader>
    <h3>Upload CV</h3>
  </CardHeader>
  <CardContent>
    <p>Drag and drop your CV here</p>
  </CardContent>
  <CardFooter>
    <Button>Browse Files</Button>
  </CardFooter>
</Card>
```

### 4. Progress Component

**File**: `src/components/ui/progress.tsx`

```typescript
interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
  max?: number
  variant?: 'default' | 'success' | 'warning' | 'error'
  showLabel?: boolean
}
```

**Features**:
- Animated progress bar
- Color variants for different states
- Optional percentage label
- Accessible with proper ARIA attributes

**Usage Examples**:
```typescript
<Progress value={45} max={100} showLabel />
<Progress value={100} variant="success" />
```

### 5. Badge Component

**File**: `src/components/ui/badge.tsx`

```typescript
interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline'
  size?: 'sm' | 'default' | 'lg'
}
```

**Usage Examples**:
```typescript
<Badge variant="success">Match: 85%</Badge>
<Badge variant="warning">Missing Data</Badge>
```

### 6. Dialog Component

**File**: `src/components/ui/dialog.tsx`

```typescript
interface DialogProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children: React.ReactNode
}

interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'default' | 'lg' | 'xl'
}
```

**Subcomponents**:
- `DialogTrigger`: Button or element that opens dialog
- `DialogContent`: Main dialog container
- `DialogHeader`: Title and description area
- `DialogFooter`: Action buttons area
- `DialogClose`: Close button

**Usage Examples**:
```typescript
<Dialog>
  <DialogTrigger asChild>
    <Button>View Details</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <h2>Candidate Analysis</h2>
    </DialogHeader>
    <p>Detailed analysis content...</p>
    <DialogFooter>
      <DialogClose asChild>
        <Button variant="outline">Close</Button>
      </DialogClose>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 7. Alert Component

**File**: `src/components/ui/alert.tsx`

```typescript
interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'warning' | 'success'
}

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}
```

**Features**:
- Color-coded variants for different message types
- Icon support for visual context
- Accessible with proper roles

**Usage Examples**:
```typescript
<Alert variant="destructive">
  <AlertDescription>
    Upload failed. Please try again.
  </AlertDescription>
</Alert>
```

### 8. Textarea Component

**File**: `src/components/ui/textarea.tsx`

```typescript
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
  resizable?: boolean
}
```

**Features**:
- Auto-resizing option
- Error state styling
- Consistent with Input component styling

### 9. Label Component

**File**: `src/components/ui/label.tsx`

```typescript
interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean
}
```

**Features**:
- Required field indicator (*)
- Consistent typography
- Proper association with form controls

## Composite Components

### 1. Form Field Component

**File**: `src/components/ui/form-field.tsx`

```typescript
interface FormFieldProps {
  label: string
  error?: string
  required?: boolean
  children: React.ReactNode
  description?: string
}
```

**Purpose**: Combines Label, Input/Textarea, and error message into a single component

### 2. Loading Spinner Component

**File**: `src/components/ui/loading-spinner.tsx`

```typescript
interface LoadingSpinnerProps {
  size?: 'sm' | 'default' | 'lg'
  className?: string
}
```

**Features**:
- Smooth CSS animation
- Multiple sizes
- Accessible with proper ARIA labels

### 3. File Upload Zone Component

**File**: `src/components/ui/file-upload-zone.tsx`

```typescript
interface FileUploadZoneProps {
  onFileSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
  maxSize?: number
  disabled?: boolean
  error?: string
}
```

**Features**:
- Drag and drop functionality
- File type and size validation
- Visual feedback for drag states
- Error display

## Component Testing Standards

### Unit Tests
Each component should have:
- Rendering tests for all variants
- Interaction tests for clickable elements
- Accessibility tests (ARIA attributes, keyboard navigation)
- Error state tests

### Visual Testing
- Storybook stories for all variants
- Visual regression testing
- Responsive design testing

## Accessibility Requirements

### WCAG 2.1 AA Compliance
- Color contrast ratios meet minimum requirements
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- Proper semantic HTML

### Specific Requirements
- Buttons: Proper focus states and ARIA labels
- Forms: Label associations and error announcements
- Dialogs: Focus trapping and escape key handling
- Progress: ARIA valuemin, valuemax, valuenow attributes

## Component Documentation

### Props Documentation
Each component must include:
- JSDoc comments for all props
- Usage examples
- Accessibility notes
- Migration notes for breaking changes

### Storybook Integration
All components should have:
- Default story showing basic usage
- Stories for each variant
- Interactive controls for testing
- Documentation tab with props table

## File Organization

```
src/components/ui/
├── button.tsx
├── input.tsx
├── textarea.tsx
├── card.tsx
├── progress.tsx
├── badge.tsx
├── dialog.tsx
├── alert.tsx
├── label.tsx
├── form-field.tsx
├── loading-spinner.tsx
├── file-upload-zone.tsx
├── index.ts          # Re-export all components
└── styles/
    ├── globals.css    # Global styles and CSS variables
    └── components.css # Component-specific styles
```

## Implementation Priorities

### Phase 1: Core Components
1. Button
2. Input
3. Card
4. Label
5. Form Field

### Phase 2: Interactive Components
1. Dialog
2. Progress
3. Alert
4. File Upload Zone

### Phase 3: Specialized Components
1. Badge
2. Loading Spinner
3. Textarea

## Integration with Form Libraries

### React Hook Form Integration
Components should work seamlessly with react-hook-form:
```typescript
<FormField
  label="LinkedIn URL"
  error={errors.linkedinUrl?.message}
  required
>
  <Input
    {...register('linkedinUrl')}
    error={!!errors.linkedinUrl}
    placeholder="https://linkedin.com/in/username"
  />
</FormField>
```

### Validation Display
Error states should be visually consistent across all form components and integrate with validation libraries like Zod.

This specification provides a comprehensive foundation for building a consistent, accessible, and maintainable UI component library that will serve as the basis for all user interface elements in the application.