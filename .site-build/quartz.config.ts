import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Quartz 4 Configuration
 *
 * See https://quartz.jzhao.xyz/configuration for more information.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "Covalon",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "en-US",
    baseUrl: "covalon.github.io/covalon-guide/obs-covalon-guide",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      // Matched to Obsidian's default theme (and its default purple accent) so the site looks like the vault.
      // Fonts: Obsidian uses the system font; custom.scss sets the same font stacks.
      fontOrigin: "local",
      cdnCaching: true,
      typography: {
        header: "system-ui",
        body: "system-ui",
        code: "ui-monospace",
      },
      colors: {
        lightMode: {
          // parchment colours from the original Homebrewery guide (the vault's snippet uses the same)
          light: "#f3e7cc", // page background
          lightgray: "#d7c9a8", // borders
          gray: "#4a5a8a", // faint text (muted navy)
          darkgray: "#1f1a12", // body text
          dark: "#0c246a", // headings (navy)
          secondary: "#3b62c4", // links and accent (a slightly lighter navy than the headings)
          tertiary: "#0c246a", // link hover (heading navy)
          highlight: "rgba(59, 98, 196, 0.1)",
          textHighlight: "rgba(255, 208, 0, 0.4)",
        },
        darkMode: {
          light: "#1e1e1e",
          lightgray: "#363636",
          gray: "#666666",
          darkgray: "#dadada",
          dark: "#dadada",
          secondary: "#9478f0",
          tertiary: "#a68af9",
          highlight: "rgba(148, 120, 240, 0.12)",
          textHighlight: "rgba(255, 208, 0, 0.4)",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false, parseTags: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents({ maxDepth: 4 }),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
      // Comment out CustomOgImages to speed up build time
    ],
  },
}

export default config
