// Loads Roboto Condensed (used by the statblock callouts). A stylesheet link can't go in custom.scss:
// Quartz combines all CSS into one file, where an @import would have to come first.
import { QuartzComponent, QuartzComponentConstructor } from "./types"

const ExtraFonts: QuartzComponent = () => (
  <link
    rel="stylesheet"
    href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&display=swap"
  />
)

export default (() => ExtraFonts) satisfies QuartzComponentConstructor
