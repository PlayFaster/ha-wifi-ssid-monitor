/** @type {import("prettier").Config} */
module.exports = {
  printWidth: 88,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: false,
  trailingComma: "es5",
  bracketSpacing: true,
  arrowParens: "always",
  proseWrap: "always",
  // Top-level so the plugin is available in all overrides, including the
  // manifest.json override below. HA puts this inside the JSON override, which
  // works for them because their manifests always co-match that override too.
  // Our custom_components/ structure does not, so top-level is required.
  plugins: [require.resolve("prettier-plugin-sort-json")],
  overrides: [
    {
      files: "**/*.json",
      options: {
        jsonRecursiveSort: true,
        jsonSortOrder: JSON.stringify({ [/.*/]: "numeric" }),
      },
    },
    {
      // HA HASSFEST requires: domain, name, then alphabetical.
      // This override pins domain and name at the top for all manifest files.
      files: ["manifest.json", "**/manifest.json"],
      options: {
        jsonRecursiveSort: false,
        jsonSortOrder: JSON.stringify({
          domain: null,
          name: null,
          [/.*/]: "numeric",
        }),
      },
    },
    {
      files: "*.md",
      options: {
        proseWrap: "never",
      },
    },
  ],
};
