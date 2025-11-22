# Quick Reference: Updating Templates to v2.0 Design

## 🎯 Common Patterns & Quick Wins

### Page Header

```html
<!-- OLD -->
<h1>Products</h1>
<p>Manage your inventory</p>

<!-- NEW -->
<div class="page-header mb-4">
  <div class="page-header-content">
    <h1 class="page-title">
      <i class="bi bi-box-seam gradient-text"></i>
      Products
    </h1>
    <p class="page-description">Manage your inventory products</p>
  </div>
  <div class="page-actions">
    <a href="create" class="btn btn-primary hover-scale">
      <i class="bi bi-plus-circle"></i>
      Add Product
    </a>
  </div>
</div>
```

### Cards

```html
<!-- OLD -->
<div class="card shadow">
  <div class="card-header bg-primary text-white">
    <h5>Card Title</h5>
  </div>
  <div class="card-body">Content</div>
</div>

<!-- NEW -->
<div class="card elevation-2 hover-lift">
  <div class="card-header">
    <h5>
      <i class="bi bi-icon text-primary"></i>
      Card Title
    </h5>
  </div>
  <div class="card-body">Content</div>
</div>
```

### Buttons

```html
<!-- OLD -->
<button class="btn btn-primary">Submit</button>
<button class="btn btn-outline-secondary">Cancel</button>

<!-- NEW -->
<button class="btn btn-primary hover-scale">
  <i class="bi bi-check-circle"></i>
  Submit
</button>
<button class="btn btn-outline-secondary hover-lift">
  <i class="bi bi-x-circle"></i>
  Cancel
</button>
```

### Tables

```html
<!-- OLD -->
<table class="table table-striped">
  <thead>
    <tr>
      <th>Name</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Item 1</td>
      <td><span class="badge bg-success">Active</span></td>
    </tr>
  </tbody>
</table>

<!-- NEW -->
<table class="table table-hover">
  <thead>
    <tr>
      <th>Name</th>
      <th>Status</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr class="hover-lift-row">
      <td><strong>Item 1</strong></td>
      <td><span class="badge badge-success">Active</span></td>
      <td>
        <button class="btn btn-sm btn-outline-primary hover-scale">
          <i class="bi bi-pencil"></i>
        </button>
      </td>
    </tr>
  </tbody>
</table>
```

### Badges

```html
<!-- OLD -->
<span class="badge bg-success">Active</span>
<span class="badge bg-danger">Inactive</span>

<!-- NEW -->
<span class="badge badge-success">Active</span>
<span class="badge badge-danger">Inactive</span>
<span class="badge badge-warning-soft">Pending</span>
```

### Form Fields

```html
<!-- OLD -->
<label for="name">Product Name</label>
<input type="text" class="form-control" id="name" name="name" />

<!-- NEW -->
<label for="name" class="form-label fw-semibold">
  <i class="bi bi-box text-primary"></i>
  Product Name
</label>
<input
  type="text"
  class="form-control"
  id="name"
  name="name"
  placeholder="Enter product name"
  required
/>
<div class="invalid-feedback">Please enter a product name</div>
```

### Alerts

```html
<!-- OLD -->
<div class="alert alert-success">Operation successful!</div>

<!-- NEW -->
<div class="alert alert-success elevation-2">
  <i class="bi bi-check-circle-fill"></i>
  Operation successful!
</div>
```

### Empty States

```html
<!-- NEW PATTERN -->
<div class="empty-state">
  <div class="empty-state-icon">
    <i class="bi bi-inbox"></i>
  </div>
  <div class="empty-state-title">No products found</div>
  <div class="empty-state-description">
    Start by adding your first product to the inventory
  </div>
  <a href="create" class="btn btn-primary hover-scale mt-3">
    <i class="bi bi-plus-circle"></i>
    Add First Product
  </a>
</div>
```

### Loading States

```html
<!-- Spinner -->
<div class="loading-spinner">
  <div class="spinner"></div>
  <p>Loading...</p>
</div>

<!-- Skeleton -->
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-title"></div>
<div class="skeleton skeleton-avatar"></div>
```

---

## 🎨 Animation Classes Reference

### Entrance Animations

- `animate-fade-in` - Fade in
- `animate-fade-in-up` - Fade in from bottom
- `animate-fade-in-down` - Fade in from top
- `animate-slide-in-up` - Slide from bottom
- `animate-slide-in-left` - Slide from left
- `animate-scale-in` - Scale up
- `animate-bounce-in` - Bounce entrance

### Hover Effects

- `hover-lift` - Lifts element on hover (translateY + shadow)
- `hover-scale` - Scales element to 1.05
- `hover-rotate` - Slight rotation
- `hover-glow` - Glow effect
- `hover-shadow` - Increases shadow

### Container Animations

```html
<div class="stagger-container">
  <div class="stagger-item">Item 1</div>
  <!-- 0s delay -->
  <div class="stagger-item">Item 2</div>
  <!-- 0.1s delay -->
  <div class="stagger-item">Item 3</div>
  <!-- 0.2s delay -->
</div>
```

### Delays & Durations

- `delay-100` to `delay-500` (100ms to 500ms)
- `duration-150` to `duration-1000` (150ms to 1s)

---

## 🎨 Color Utilities

### Text Colors

```html
<span class="text-primary-600">Primary text</span>
<span class="text-success-500">Success text</span>
<span class="text-danger-600">Danger text</span>
<span class="text-gray-500">Muted text</span>
```

### Background Colors

```html
<div class="bg-primary-50">Light primary background</div>
<div class="bg-success-100">Light success background</div>
<div class="bg-gradient-primary">Gradient background</div>
```

### Gradient Text

```html
<h1 class="gradient-text">Gradient Heading</h1>
```

---

## 📏 Spacing Utilities

### Margin/Padding

```html
<div class="m-0">No margin</div>
<div class="m-1">0.25rem margin</div>
<div class="m-4">1rem margin</div>
<div class="mb-8">2rem bottom margin</div>
<div class="p-6">1.5rem padding</div>
```

---

## 🎯 Elevation (Shadows)

```html
<div class="elevation-0">No shadow</div>
<div class="elevation-1">Subtle shadow</div>
<div class="elevation-2">Small shadow (default for cards)</div>
<div class="elevation-3">Medium shadow</div>
<div class="elevation-4">Large shadow (auth cards)</div>
<div class="elevation-5">Extra large shadow</div>
```

---

## ♿ Accessibility Checklist for Each Template

- [ ] Add `aria-label` to icon-only buttons
- [ ] Use `aria-hidden="true"` on decorative icons
- [ ] Include `aria-current="page"` on active nav items
- [ ] Add `aria-describedby` to link error messages to inputs
- [ ] Use semantic HTML (`<nav>`, `<main>`, `<article>`, `<aside>`)
- [ ] Ensure all form inputs have associated `<label>` elements
- [ ] Add `role="alert"` to dynamic error messages
- [ ] Include skip links where appropriate
- [ ] Test keyboard navigation (Tab, Enter, Esc)
- [ ] Verify color contrast ratios (minimum 4.5:1)

---

## 🔧 Quick Template Update Workflow

### Step 1: Update Container

```html
<!-- Wrap content in container with animation -->
<div class="container-fluid animate-fade-in">
  <!-- Your content -->
</div>
```

### Step 2: Update Page Header

```html
<!-- Add modern page header -->
<div class="page-header mb-4">
  <div class="page-header-content">
    <h1 class="page-title">
      <i class="bi bi-icon gradient-text"></i>
      Page Title
    </h1>
    <p class="page-description">Description</p>
  </div>
  <div class="page-actions">
    <button class="btn btn-primary hover-scale">Action</button>
  </div>
</div>
```

### Step 3: Update Cards

```html
<!-- Add elevation and hover effects -->
<div class="card elevation-2 hover-lift">
  <div class="card-header">
    <h5>
      <i class="bi bi-icon text-primary"></i>
      Card Title
    </h5>
  </div>
  <div class="card-body">
    <!-- Content -->
  </div>
</div>
```

### Step 4: Update Buttons

```html
<!-- Add icons and hover effects -->
<button class="btn btn-primary hover-scale">
  <i class="bi bi-check"></i>
  Submit
</button>
```

### Step 5: Update Badges

```html
<!-- Use new badge classes -->
<span class="badge badge-success">Active</span>
<span class="badge badge-warning-soft">Pending</span>
```

### Step 6: Add Animations

```html
<!-- Add stagger animations to lists -->
<div class="row stagger-container">
  <div class="col-md-4 stagger-item">Card 1</div>
  <div class="col-md-4 stagger-item">Card 2</div>
  <div class="col-md-4 stagger-item">Card 3</div>
</div>
```

### Step 7: Test Responsiveness

- Preview at 375px (mobile)
- Preview at 768px (tablet)
- Preview at 1920px (desktop)

---

## 📋 Template Priority List

### 🔴 High Priority (User-Facing CRUD)

1. **products/list.html**
   - Update table with hover effects
   - Add modern badges for stock status
   - Enhance filter card
2. **products/create.html**

   - Improve form layout
   - Add validation feedback
   - Better button styling

3. **warehouses/list.html**

   - Modern table design
   - Action buttons with icons

4. **warehouses/create.html**
   - Form enhancements
   - Validation states

### 🟡 Medium Priority (Operations)

5. **receipts/list.html**
   - Status badges
   - Date formatting
6. **receipts/create.html**
   - Multi-step form
   - Line items table
7. **deliveries/list.html**
   - Similar to receipts
8. **transfers/list.html**
   - Status tracking UI

### 🟢 Low Priority (Supporting Pages)

9. **stock/levels.html**
   - Data visualization
10. **stock/ledger.html**
    - Transaction history
11. **auth/register.html**
    - Form improvements
12. **errors/\*.html**
    - Friendly error pages

---

## 💡 Pro Tips

1. **Always add hover effects** to interactive elements:

   ```html
   <button class="btn btn-primary hover-scale">Button</button>
   <div class="card hover-lift">Card</div>
   ```

2. **Use stagger animations** for lists:

   ```html
   <div class="stagger-container">
     <div class="stagger-item">Item</div>
   </div>
   ```

3. **Add gradient text to icons** in headers:

   ```html
   <i class="bi bi-icon gradient-text"></i>
   ```

4. **Use elevation for visual hierarchy**:

   - Cards: `elevation-2`
   - Modals: `elevation-5`
   - Auth cards: `elevation-4`

5. **Include icons in labels** for better UX:

   ```html
   <label class="form-label">
     <i class="bi bi-icon text-primary"></i>
     Label Text
   </label>
   ```

6. **Always add invalid-feedback** to form fields:
   ```html
   <input class="form-control" required />
   <div class="invalid-feedback">Error message</div>
   ```

---

## 🎉 You're Ready!

Use this guide to systematically update each template. The design system handles all the complexity - you just need to apply the right classes!

**Questions?** Check the full design system documentation in `design-system.css` or refer to `FRONTEND_REDESIGN_SUMMARY.md`.
