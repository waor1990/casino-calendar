# AI Agent Instructions for `assets/styles`

**🚨 CRITICAL: NEVER EDIT `../style.css` DIRECTLY! IT IS AUTO-GENERATED AND WILL BE OVERWRITTEN! 🚨**

SCSS partials in this folder are combined into `../style.scss` and compiled to `../style.css`.

**See root `AGENTS.md` and `.github/copilot-instructions.md` for comprehensive guidelines.**

## ⚠️ MANDATORY CSS WORKFLOW ⚠️

**ALL CSS changes must be made in SCSS files in this directory. The `style.css` file is generated automatically and any direct edits will be lost.**

## File Structure

- `_variables.scss` - Design tokens (colors, spacing, breakpoints)
- `_mixins.scss` - Reusable SCSS mixins and functions
- `_layout.scss` - Main layout and grid styles
- `_components.scss` - Component-specific styles
- `_calendar_grid.scss` - Calendar grid layout
- `_modal.scss` - Modal dialog styles
- `_utilities.scss` - Utility classes
- `_animations.scss` - CSS animations and transitions

## Development Workflow

### CSS Compilation

**⚠️ REMINDER: Only edit SCSS files! The `style.css` file is auto-generated!**

- Use BEM-like class names and keep selectors narrow
- Place design tokens in `_variables.scss` and reusable code in `_mixins.scss`
- After editing SCSS files, regenerate `style.css` using the unified script (`npm run build:css`)
- It outputs the same file watched by `npm run watch:css` and is used in deployment
- The app automatically builds CSS when started, so manual compilation is optional
- If `sass` is installed globally you can also run it directly:

  ```bash
  npm run build:css
  npm run watch:css   # optional for auto-rebuild
  sass ../style.scss ../style.css
  ```

**🚨 NEVER commit changes to `style.css` - it will be regenerated automatically!**

### Linting

- Run `npm run lint:css` (check) before committing style changes; use `npm run lint:css:fix` to auto-correct formatting issues
- Configuration in `config/.stylelintrc.json`
- Follows standard SCSS conventions

## Key Patterns

### Component Naming

Follow BEM-like naming conventions:

- `.week-grid` - Block-level components
- `.event-block-grid` - Grid-specific blocks
- `.casino-legend__item` - Element within block
- `.modal--active` - Modifier states

### Responsive Design

- Mobile-first approach with breakpoints in `_variables.scss`
- Use CSS Grid for layout components
- Flexbox for component-level alignment

### Color System

- Use CSS custom properties defined in `_variables.scss`
- Casino-specific colors loaded from JSON data
- Dark/light theme support via CSS variables

## Important Notes

**🚨 ABSOLUTELY CRITICAL: Never edit `../style.css` directly - it's auto-generated and will be overwritten! 🚨**

- **ALL styling changes must be made in SCSS files in this directory**
- Do not commit compiled CSS changes if the only updates are in SCSS
- The `style.css` file is regenerated every time the app starts
- Always test responsive behavior across device sizes
- Maintain accessibility standards (contrast ratios, focus states)
- **Any direct edits to `style.css` will be permanently lost on next build**

*[End of styles guidelines]*
