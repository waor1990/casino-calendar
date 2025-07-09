# AGENTS instructions for `assets/styles`

SCSS partials in this folder are combined into `../style.scss` and compiled to `../style.css`.

- Use BEM-like class names and keep selectors narrow.
- Place design tokens in `_variables.scss` and reusable code in `_mixins.scss`.
- After editing SCSS files, regenerate `style.css` if the `sass` command is available:

  ```bash
  npm run build:css
  npm run watch:css # optional for auto-rebuild
  sass ../style.scss ../style.css
  ```

- Do not commit compiled CSS changes if the only updates are in SCSS.

*[End of styles guidelines]*
