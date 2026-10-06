# Dashboard design contract

The page explains one verified flow: Sparkplug B telemetry enters through the
source broker, Expanso Edge applies the shipped policy, and HiveMQ receives the
secured outputs.

## Required order

1. Explain the outcome and its proof boundary.
2. Show the source, Edge, Cloud control lane, and HiveMQ topology.
3. Explore every pipeline stage with real fixture input and output.
4. Give local run, repository verification, and Cloud deployment instructions.

## Interaction contract

- Light mode loads by default and the header has an explicit dark-mode toggle.
- Left and Right page the explorer without changing the scroll position.
- Copy and download results appear beside the control that was used, including
  failure feedback.
- JSON is vertically formatted.
- The page has no horizontal overflow at 320, 400, 768, or 1440 pixels.
- Text and controls meet WCAG AA contrast in both themes.

## Truth contract

The browser loads `fixtures/stages.json` and the shipped pipeline file. It does
not calculate fake savings, generate random validation failures, or claim that
fixture playback is live broker traffic. Local Compose acceptance and Cloud
execution remain separate proof states.

The topology may animate direction of travel. Motion must remain calm and must
not imply that a run occurred. The page uses no gradients, decorative grids,
side stripes, or externally hosted assets.
