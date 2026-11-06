# Light UI refinement

This is an operational document workbench. Preserve the existing authenticated workflows, model controls, workspace permissions, source evidence, answer verification, and multi-model inspection.

The user supplied a blue-and-white reference with lime actions and requested a lighter interface. Use white panels, a pale cool-gray workspace, blue brand accents, dark blue-gray text, and lime primary question/sign-in actions. Keep verification colors semantic, with pale backgrounds and dark readable text. The sign-in page carries the strongest blue surface; reading and research areas stay light.

Use the existing sans-serif typography with an Avenir Next/DM Sans stack. Display copy has compact line height and restrained negative tracking; operational labels remain small and readable. Keep the source library distinct from the conversation area. Source documents, models, and status controls should wrap cleanly on small screens. Interactive elements have visible keyboard focus.

The `?preview=1` route uses a separate fixture adapter and a persistent sample-data notice. Never imply its sample documents, response scores, or model state are live. Preserve normal API access at `/`.

Verified at 1440px and 390px with browser screenshots and question-flow checks. The preview sends no API requests. The frontend build passes. Full-stack and live-model validation require the unavailable Docker stack and a running model endpoint.
