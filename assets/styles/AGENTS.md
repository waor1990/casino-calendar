# AI Agent Instructions for `assets/styles`

SCSS partials in this folder are combined into `../style.scss` and compiled to `../style.css`.

**See root `AGENTS.md` and `.github/copilot-instructions.md` for comprehensive guidelines.**

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

- Use BEM-like class names and keep selectors narrow
- Place design tokens in `_variables.scss` and reusable code in `_mixins.scss`
- After editing SCSS files, regenerate `style.css` using the unified script (`npm run build:css`)
- It outputs the same file watched by `npm run watch:css` and is used in deployment
- If `sass` is installed globally you can also run it directly:

  ```bash
  npm run build:css
  npm run watch:css   # optional for auto-rebuild
  sass ../style.scss ../style.css
  ```

### Linting

- Run `npm run lint:css` before committing style changes
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

- Do not commit compiled CSS changes if the only updates are in SCSS
- Always test responsive behavior across device sizes
- Maintain accessibility standards (contrast ratios, focus states)

*[End of styles guidelines]*
