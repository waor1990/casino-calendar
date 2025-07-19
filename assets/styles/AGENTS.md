# AGENTS instructions for `assets/styles`

SCSS partials in this folder are combined into `../style.scss` and compiled to
`../style.css`.

- Use BEM-like class names and keep selectors narrow.
- Place design tokens in `_variables.scss` and reusable code in `_mixins.scss`.
- After editing SCSS files, regenerate `style.css` using the unified script
  (`npm run build:css`). It outputs the same file watched by `npm run watch:css`
  and is used in deployment. If `sass` is installed globally you can also run it
  directly:

  ```bash
  npm run build:css
  npm run watch:css   # optional for auto-rebuild
  sass ../style.scss ../style.css
  ```

- Do not commit compiled CSS changes if the only updates are in SCSS.

*[End of styles guidelines]*
