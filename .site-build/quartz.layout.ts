import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"
// Covalon components (copied from .site-build/components into quartz/components at build time)
import PagefindSearch from "./quartz/components/PagefindSearch"
import FilterableTables from "./quartz/components/FilterableTables"
import ExtraFonts from "./quartz/components/ExtraFonts"

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [PagefindSearch(), FilterableTables(), ExtraFonts()],
  footer: Component.Footer({
    links: {
      "Join Covalon": "https://discord.gg/covalon",
      "Current guide": "https://covalon.github.io/covalon-guide/",
    },
  }),
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.ConditionalRender({
      component: Component.Breadcrumbs(),
      condition: (page) => page.fileData.slug !== "index",
    }),
    Component.ArticleTitle(),
    Component.TagList(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
        { Component: Component.ReaderMode() },
      ],
    }),
    Component.Explorer({
      // Player's Guide and GM's Guide first, with each guide's full page at the top of its folder;
      // everything else folders first, then alphabetical. (Self-contained: Quartz sends this function to the browser.)
      sortFn: (a, b) => {
        // no helper functions in here: the build would wrap them in a helper the browser doesn't have
        const order = { "Player's Guide": 0, "GM's Guide": 1, "Covalon Player's Guide": 0, "Covalon GM's Guide": 0 }
        const r = (order[a.displayName] ?? 10) - (order[b.displayName] ?? 10)
        if (r !== 0) return r
        if (a.isFolder !== b.isFolder) return a.isFolder ? -1 : 1
        return a.displayName.localeCompare(b.displayName, undefined, { numeric: true, sensitivity: "base" })
      },
    }),
  ],
  right: [
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
    Component.Graph(),
  ],
}

// components for pages that display lists of pages  (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({
      components: [
        {
          Component: Component.Search(),
          grow: true,
        },
        { Component: Component.Darkmode() },
      ],
    }),
    Component.Explorer({
      // Player's Guide and GM's Guide first, with each guide's full page at the top of its folder;
      // everything else folders first, then alphabetical. (Self-contained: Quartz sends this function to the browser.)
      sortFn: (a, b) => {
        // no helper functions in here: the build would wrap them in a helper the browser doesn't have
        const order = { "Player's Guide": 0, "GM's Guide": 1, "Covalon Player's Guide": 0, "Covalon GM's Guide": 0 }
        const r = (order[a.displayName] ?? 10) - (order[b.displayName] ?? 10)
        if (r !== 0) return r
        if (a.isFolder !== b.isFolder) return a.isFolder ? -1 : 1
        return a.displayName.localeCompare(b.displayName, undefined, { numeric: true, sensitivity: "base" })
      },
    }),
  ],
  right: [],
}
