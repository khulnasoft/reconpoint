
# reconPoint Design System & Styling Guide

## Overview

This document outlines the comprehensive design improvements made to the reconPoint web interface, including new CSS frameworks, utility classes, component enhancements, and best practices for maintaining visual consistency.

---

## 📋 Design System Tokens

### Color Palette

#### Primary Colors
- **Primary**: `#3283f6` - Main brand color
- **Primary Dark**: `#1e5bc4` - Darker shade for hover states
- **Primary Light**: `#5fa3ff` - Lighter shade for backgrounds

#### Semantic Colors
- **Danger**: `#dc3545` - Error/delete actions
- **Success**: `#198754` - Confirmation/positive actions
- **Warning**: `#ffc107` - Caution/warning states
- **Info**: `#0dcaf0` - Information messages

#### Severity Levels
- **Critical**: `#E53935` - Highest severity issues
- **High**: `#FF6F00` - High severity
- **Medium**: `#FFB300` - Medium severity
- **Low**: `#FDD835` - Low severity

#### Neutral Colors
- **Light**: `#f8f9fa` - Background
- **Border**: `#e9ecef` - Neutral borders
- **Muted Text**: `#6c757d` - Secondary text
- **Dark Text**: `#212529` - Primary text

### Typography Scale

```
--font-size-xs:   0.75rem   (12px)
--font-size-sm:   0.875rem  (14px)
--font-size-base: 1rem      (16px)
--font-size-lg:   1.125rem  (18px)
--font-size-xl:   1.25rem   (20px)
--font-size-2xl:  1.5rem    (24px)
--font-size-3xl:  1.875rem  (30px)
```

### Spacing Scale

```
--spacing-xs:   0.25rem  (4px)
--spacing-sm:   0.5rem   (8px)
--spacing-md:   1rem     (16px)
--spacing-lg:   1.5rem   (24px)
--spacing-xl:   2rem     (32px)
--spacing-2xl:  3rem     (48px)
```

### Border Radius

```
--radius-xs:    0.25rem
--radius-sm:    0.375rem
--radius-md:    0.5rem
--radius-lg:    0.75rem
--radius-xl:    1rem
--radius-full:  9999px
```

### Shadows

```
--shadow-xs:  0 1px 2px rgba(0,0,0,0.05)
--shadow-sm:  0 1px 3px rgba(0,0,0,0.1)
--shadow-md:  0 4px 6px rgba(0,0,0,0.1)
--shadow-lg:  0 10px 15px rgba(0,0,0,0.1)
--shadow-xl:  0 20px 25px rgba(0,0,0,0.1)
```

---

## 🎨 Component Styling

### Buttons

#### Primary Button
```html
<button class="btn btn-primary">Action</button>
```
- Gradient background from primary to primary-dark
- Elevated on hover with shadow
- Smooth transitions

#### Button Sizes
```html
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Medium</button>
<button class="btn btn-primary btn-lg">Large</button>
```

#### Icon Button
```html
<button class="btn btn-icon"><i class="fe-plus"></i></button>
<button class="btn btn-icon btn-icon-sm"><i class="fe-x"></i></button>
```

### Forms

#### Text Input
```html
<input type="text" class="form-control" placeholder="Enter text">
```
- Clean border with focus ring
- Smooth transitions on focus
- Validation states with icons

#### Form Labels
```html
<label class="form-label">Field Label</label>
<input type="text" class="form-control">
```

#### Validation States
```html
<!-- Valid -->
<input type="text" class="form-control is-valid">
<div class="valid-feedback">Looks good!</div>

<!-- Invalid -->
<input type="text" class="form-control is-invalid">
<div class="invalid-feedback">Please provide a valid value.</div>
```

#### Required Field Indicator
```html
<label class="form-label required">Required Field</label>
```
- Asterisk automatically added
- Red color matches validation

### Cards

#### Basic Card
```html
<div class="card">
  <div class="card-header">Card Title</div>
  <div class="card-body">Card content goes here</div>
  <div class="card-footer">Footer content</div>
</div>
```

#### Accent Card
```html
<div class="card card-primary">
  <div class="card-header">Primary Card</div>
  <div class="card-body">Highlighted content</div>
</div>
```

#### Compact Card
```html
<div class="card card-compact">
  <div class="card-body">Compact spacing</div>
</div>
```

### Badges

#### Status Badges
```html
<span class="badge badge-primary">Primary</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-danger">Danger</span>
```

#### Severity Badges
```html
<span class="badge badge-critical">Critical</span>
<span class="badge badge-high">High</span>
<span class="badge badge-medium">Medium</span>
<span class="badge badge-low">Low</span>
```

#### Soft Badges
```html
<span class="badge-soft-info">Info</span>
<span class="badge-soft-warning">Warning</span>
<span class="badge-soft-success">Success</span>
```

#### Outline Badge
```html
<span class="badge badge-primary badge-outline">Outlined</span>
```

#### Badge Sizes
```html
<span class="badge badge-sm">Small</span>
<span class="badge">Medium</span>
<span class="badge badge-lg">Large</span>
```

### Modals

```html
<div class="modal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Modal Title</h5>
        <button type="button" class="btn-close"></button>
      </div>
      <div class="modal-body">
        Modal content goes here
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary">Close</button>
        <button type="button" class="btn btn-primary">Save</button>
      </div>
    </div>
  </div>
</div>
```

### Alerts

#### Alert Types
```html
<div class="alert alert-primary">Primary alert</div>
<div class="alert alert-success">Success alert</div>
<div class="alert alert-danger">Danger alert</div>
<div class="alert alert-warning">Warning alert</div>
<div class="alert alert-info">Info alert</div>
```

#### Dismissible Alert
```html
<div class="alert alert-warning alert-dismissible fade show">
  <strong>Warning!</strong> This is a dismissible alert.
  <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
```

### Data Tables

```html
<table class="table">
  <thead>
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data</td>
      <td>Data</td>
    </tr>
  </tbody>
</table>
```

**Enhancements:**
- Professional header styling with uppercase labels
- Hover effects on rows
- Active row highlighting
- Smooth sorting transitions

---

## 🎭 Responsive Design

### Breakpoints
- **Mobile**: < 576px
- **Tablet**: 576px - 768px
- **Desktop**: 768px - 992px
- **Large**: 992px - 1200px
- **XL**: > 1200px

### Responsive Utilities
```html
<!-- Display utilities -->
<div class="d-flex-center">Centered content</div>
<div class="d-flex-between">Space between items</div>

<!-- Responsive spacing -->
<div class="mb-lg">Margin bottom (large)</div>
<div class="p-md">Padding (medium)</div>

<!-- Mobile-first hiding -->
<div class="d-none d-md-block">Hidden on mobile</div>
```

---

## 🌙 Dark Mode Support

The design system includes comprehensive dark mode support via the CSS variable fallback pattern:

```css
/* Light mode (default) */
:root {
  --color-light: #f8f9fa;
  --color-text-dark: #212529;
}

/* Dark mode */
[data-bs-theme="dark"] {
  --color-light: #1a1d29;
  --color-text-dark: #f3f4f6;
}
```

All components automatically adapt to dark mode through CSS variables.

---

## ✨ Animations & Transitions

### Built-in Animations

#### Fade
```html
<div class="transition-fast">Fades smoothly</div>
```

#### Slide
Uses keyframe animations:
- `slideInUp` - Slide in from bottom
- `slideInDown` - Slide in from top
- `slideInLeft` - Slide in from left
- `slideInRight` - Slide in from right

#### Scale
```html
<div class="transition-slow">Scales smoothly</div>
```

### Transition Classes
```html
<!-- Fast transition (150ms) -->
<button class="btn transition-fast"></button>

<!-- Base transition (200ms) -->
<button class="btn transition-base"></button>

<!-- Slow transition (300ms) -->
<button class="btn transition-slow"></button>

<!-- Specific properties -->
<div class="transition-colors">Color changes smoothly</div>
<div class="transition-transform">Transforms smoothly</div>
<div class="transition-shadow">Shadow changes smoothly</div>
```

### Reduced Motion Support
Automatically respects user's `prefers-reduced-motion` setting for accessibility.

---

## ♿ Accessibility Features

### Focus Indicators
```html
<!-- Automatically styled focus rings -->
<button>Click me (Tab to see focus)</button>
```

### Color Contrast
All color combinations meet WCAG AA standards (4.5:1 for text).

### Semantic HTML
```html
<!-- Use semantic elements -->
<button class="btn">Action</button>  <!-- Not <a> or <div> -->
<nav>Navigation</nav>                 <!-- Not <div> -->
<section>Content</section>             <!-- Proper structure -->
```

### ARIA Labels
```html
<button aria-label="Close menu">
  <i class="fe-x"></i>
</button>
```

---

## 📱 Utility Classes

### Text Utilities
```html
<p class="text-xs">Extra small text</p>
<p class="text-sm">Small text</p>
<p class="text-base">Base text</p>
<p class="text-lg">Large text</p>

<p class="font-light">Light weight</p>
<p class="font-regular">Regular weight</p>
<p class="font-medium">Medium weight</p>
<p class="font-semibold">Semibold weight</p>
<p class="font-bold">Bold weight</p>
```

### Spacing Utilities
```html
<!-- Margin -->
<div class="m-md">Margin all sides</div>
<div class="mt-lg">Margin top</div>
<div class="mb-sm">Margin bottom</div>

<!-- Padding -->
<div class="p-lg">Padding all sides</div>
<div class="px-md">Padding horizontal</div>
<div class="py-sm">Padding vertical</div>
```

### Border Radius
```html
<div class="rounded-xs">Extra small corners</div>
<div class="rounded-md">Medium corners</div>
<div class="rounded-xl">Extra large corners</div>
<div class="rounded-full">Fully rounded</div>
```

### Shadow Utilities
```html
<div class="shadow-xs">Extra small shadow</div>
<div class="shadow-md">Medium shadow</div>
<div class="shadow-lg">Large shadow</div>
<div class="shadow-xl">Extra large shadow</div>
```

### Flex Utilities
```html
<div class="d-flex-center">Centered flex</div>
<div class="d-flex-between">Space between</div>
<div class="gap-md">Gap between items</div>
```

### Overflow Utilities
```html
<div class="truncate">Truncates with ellipsis</div>
<div class="line-clamp-1">Single line clamp</div>
<div class="line-clamp-2">Two line clamp</div>
<div class="overflow-auto">Scrollable if needed</div>
```

---

## 🎯 Best Practices

### 1. Use Design Tokens
Always use CSS variables instead of hardcoding values:

```css
/* ❌ Bad */
color: #3283f6;
padding: 16px;

/* ✅ Good */
color: var(--color-primary);
padding: var(--spacing-md);
```

### 2. Maintain Visual Hierarchy
```html
<!-- ✅ Good hierarchy -->
<h1 class="page-title">Main Title</h1>
<h2>Section Header</h2>
<h3>Subsection</h3>
<p>Body text</p>
<small class="text-muted">Small helper text</small>
```

### 3. Consistent Spacing
```html
<!-- ✅ Consistent spacing -->
<div class="card">
  <div class="card-header mt-lg">Title</div>
  <div class="card-body mb-lg">Content</div>
</div>
```

### 4. Semantic Color Usage
```html
<!-- ✅ Semantic colors -->
<span class="badge badge-success">Success</span>
<span class="badge badge-danger">Error</span>
<button class="btn btn-primary">Action</button>
<button class="btn btn-secondary">Cancel</button>
```

### 5. Responsive First
```html
<!-- ✅ Mobile-first responsive -->
<div class="p-sm p-md-lg mb-lg mb-xl-2xl">
  Mobile small padding, desktop larger padding
</div>
```

### 6. Accessibility
```html
<!-- ✅ Good accessibility -->
<label for="email">Email</label>
<input id="email" type="email" class="form-control">

<!-- ✅ Good focus states -->
<button class="btn">Copy</button> <!-- Focus ring automatic -->
```

---

## 🚀 CSS Files Breakdown

### Core Files
1. **design-improvements.css** - Design tokens, typography, buttons, forms, cards, badges, tables, modals, alerts, navigation, loading states, utilities
2. **components-advanced.css** - Advanced form components, data tables, tabs, accordions, lists, progress bars, breadcrumbs, dropdowns, tooltips, pagination, spinners
3. **animations.css** - Smooth animations, transitions, loading states, dark mode animations
4. **badges.css** - Enhanced badge styles with hover effects and status indicators

### Load Order (in base.html)
1. `custom.css` (existing, legacy)
2. `badges.css` (enhanced)
3. `design-improvements.css` (new tokens & base components)
4. `components-advanced.css` (advanced components)
5. `animations.css` (micro-interactions)

---

## 📊 File Sizes & Performance

- **design-improvements.css**: ~30KB (extensive design system)
- **components-advanced.css**: ~20KB (component enhancements)
- **animations.css**: ~18KB (animations & transitions)
- **badges.css**: ~4KB (badge styles)

**Total**: ~72KB (minified: ~45KB, gzipped: ~12KB)

---

## 🔄 Migration Guide

### Updating Existing Components

#### Buttons
```html
<!-- Old -->
<button class="btn btn-primary" style="padding: 10px 20px;">Button</button>

<!-- New -->
<button class="btn btn-primary">Button</button>
<!-- Automatically gets proper spacing from design system -->
```

#### Form Controls
```html
<!-- Old -->
<input type="text" class="form-control" style="border-radius: 4px;">

<!-- New -->
<input type="text" class="form-control">
<!-- Automatically gets proper radius and focus states -->
```

#### Cards
```html
<!-- Old -->
<div class="card" style="box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

<!-- New -->
<div class="card">
<!-- Automatically gets proper shadow and hover effects -->
```

---

## 📝 Maintenance Notes

- All utilities use CSS custom properties for easy theming
- Dark mode is automatic via `[data-bs-theme="dark"]` attribute
- Animations respect `prefers-reduced-motion` setting
- All colors meet WCAG AA contrast standards
- Font sizes use rem units for accessibility

---

## 🐛 Troubleshooting

### Components Not Styled
1. Check CSS file load order in base.html
2. Verify browser console for load errors
3. Clear browser cache

### Animations Not Working
1. Check if `prefers-reduced-motion` is enabled
2. Verify animations.css is loaded
3. Check browser compatibility

### Dark Mode Not Working
1. Ensure ElementBootstrap theme toggle sets `data-bs-theme`
2. Verify dark mode wrapper has correct attribute
3. Clear cache and reload

---

## 🔗 References

- Bootstrap 5 Documentation: https://getbootstrap.com/docs/5.0/
- CSS Custom Properties: https://developer.mozilla.org/en-US/docs/Web/CSS/--*
- WCAG Accessibility: https://www.w3.org/WAI/test-evaluate/
- CSS Animations: https://developer.mozilla.org/en-US/docs/Web/CSS/animation

---

**Last Updated**: 2024
**Design System Version**: 1.0
**Bootstrap Version**: 5.x
