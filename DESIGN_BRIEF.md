# Demo Page Redesign Brief

## Objective

Redesign the demo webpage so it feels like a presentation-quality product story, not a generic web dashboard.

The page exists to explain one thing with clarity:

**Expanso sits in the data path between industrial SCADA systems and HiveMQ, and as the demo progresses, the architecture should visibly show what Expanso is doing.**

This needs to feel legible, deliberate, and persuasive. Think keynote-slide clarity, not admin console density.

## Core Story

The demo narrative is progressive:

1. Start with raw telemetry flowing from SCADA systems toward HiveMQ.
2. Introduce Expanso into that path.
3. Turn on capabilities one by one:
   - deadband
   - schema validation
   - compression
   - fan-out
4. As each capability is enabled, the architecture itself should change to show the new behavior.
5. The page should make the viewer understand the system just by looking at it, even before reading numbers.

The architecture is the hero.
The metrics are supporting proof.

## Visual Direction

The current page looks too much like a rough internal dashboard. That is the wrong direction.

The redesign should feel:

- presentation-grade
- high-clarity
- structured
- modern but not trendy
- confident
- visually sparse where possible
- intentional in hierarchy

It should not feel:

- like an admin panel
- like a default SaaS dashboard
- like a hackathon prototype
- like a developer tool
- like a toy diagram with random boxes

The standard to aim for is Steve Jobs style clarity:

- one obvious idea at a time
- strong hierarchy
- minimal clutter
- every visual element earns its place
- motion explains behavior
- labels are simple and human-readable

## Architecture Requirements

The top section of the page must be a real architecture diagram, not a banner with a few boxes.

It should roughly resemble the reference image already discussed:

- collection area on the left
- ingestion area on the right
- clearly boxed architectural regions
- enterprise / systems-diagram composition
- left-to-right flow

The rough structure should be:

1. **Collection / Edge / Site SCADA zone**
   - wind
   - solar
   - battery
   - distributed generation or similar grouped industrial sources

2. **Edge collection / processing layer**
   - this is where Expanso must be layered in
   - it should feel integrated into the stack, not bolted on
   - if other edge components are shown, Expanso should still be visually central to policy/data handling

3. **Ingestion zone**
   - HiveMQ as broker / data stream destination
   - timeseries flow should be obvious
   - metadata / tags / archive routing should appear when relevant

The diagram should make it obvious where Expanso lives and why it matters.

## Progressive Behavior Requirements

This is not a static architecture illustration.

As the demo progresses, the architecture must visibly evolve.

### Base state

- raw telemetry flows from SCADA to HiveMQ
- Expanso is present in the architecture, but not fully “lit up”
- the system should read as a normal ingestion pipeline

### Deadband enabled

- show that some data is suppressed before continuing downstream
- this should be understandable visually, not only numerically
- examples:
  - reduced pulse count
  - filtered stream
  - thinning message flow
  - dropped/noise path subtly indicated

### Schema validation enabled

- show that Expanso is inspecting / validating payloads
- show that bad data is blocked before HiveMQ
- optionally surface metadata / validation overlay / quality gate treatment

### Compression enabled

- show that the payload stream is being reduced or compacted
- the viewer should intuit “same information, fewer bytes”
- compression should feel like a transformation, not just a badge turning green

### Fan-out enabled

- show one stream becoming multiple destinations
- archive or secondary topic path should become visible
- the branching should feel architecturally intentional

### Metadata / tag behavior

- when relevant, metadata/tag flows should appear in the architecture
- this should be visually distinct from the primary timeseries path

## Animation Requirements

Data flow should be animated.

But the animation must explain behavior, not just decorate the page.

Good animation goals:

- make direction obvious
- make activation obvious
- make filtering obvious
- make branching obvious
- make the diagram feel alive during the demo

Avoid:

- arbitrary pulsing everywhere
- loading-spinner energy
- noisy particle effects with no meaning
- animations that compete with readability

Motion should feel calm, clean, and informative.

## Information Hierarchy

The architecture should dominate the page.

Metrics still matter, but they are secondary.

Recommended hierarchy:

1. architecture / system flow
2. active feature state
3. key proof metrics
4. detailed message/event log

The viewer should be able to glance at the page and immediately answer:

- what systems are involved?
- where does Expanso sit?
- what is data doing right now?
- what changed when the feature turned on?

## Demo Controls

The existing progressive controls still matter.

The page should support the live story around:

- default flow
- Expanso in-line behavior
- Expanso parallel / fan-out behavior

Toggles or controls for the features should remain usable, but they should be visually subordinate to the architecture.

They should feel like demo controls, not like settings forms.

## Metrics / Supporting Evidence

The supporting metrics should still show the impact of the feature progression.

Important metrics include:

- messages in
- messages out
- messages dropped
- validation failures
- bytes in
- bytes out
- saved percent
- archive topic active / off

The metrics should reinforce the architecture story, not compete with it.

The page should not open with “three equal dashboard panels” as the main composition.

## Technical Constraints

The repository context matters.

The repo does **not** currently contain the backend service directories that the original `docker-compose.yml` referenced.

That means:

- the demo should work without assuming the missing SCADA / Expanso service implementations are present locally
- the current runnable path is effectively a self-contained dashboard experience
- `./run-demo.sh` must succeed
- `./stop-demo.sh` must succeed

The design work should respect that reality.

Do not design something that only works if nonexistent backend services are magically restored.

## What Failed In The Previous Attempt

The previous result missed the mark for several reasons:

1. It still felt like a web dashboard instead of a presentation-grade architecture story.
2. The architecture was too rough and not close enough to the reference composition.
3. Expanso’s role was too literal and mechanically inserted.
4. The progressive feature behavior existed, but lacked taste and clarity.
5. The page did not have the level of visual refinement needed for a recorded demo.
6. The motion was not expressive enough to carry the story cleanly.

The redesign needs to correct those issues, not merely rearrange them.

## Design Principles

Use these principles when making decisions:

1. **Make the architecture the hero.**
2. **Show one clear idea at a time.**
3. **Prefer fewer, stronger visual moves.**
4. **Use motion to explain system behavior.**
5. **Make Expanso feel essential, not appended.**
6. **Keep controls and metrics subordinate to the story.**
7. **Design for a narrated demo recording, not just casual browsing.**

## Desired Outcome

When someone watches the demo, the page should make them feel:

- “I immediately understand the system.”
- “I can see where Expanso sits.”
- “I can see what changed when that feature turned on.”
- “This looks like a serious product story, not an internal prototype.”

## Deliverable Expectation

The redesigned page should:

- preserve the interactive demo progression
- materially improve the visual quality
- align the architecture more closely to the provided reference image
- animate the data flow in a meaningful way
- clearly show Expanso’s expanding role as features are enabled
- remain runnable in the current repo context

