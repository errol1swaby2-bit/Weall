# WeAll Protocol Architecture

## Core Layers
1. **DSL Layer**
   - Defines governance, treasury, and modular actions in YAML.
   - Example: Proposals, voting rules, quorum.

2. **Executor Layer**
   - Python runtime that interprets and enforces the DSL.
   - Ensures rules are followed automatically.

3. **Community Modules**
   - Extensions or plugins (funding models, reputation systems, content storage).
   - Future space for AI-assisted moderation or analysis.

## Design Principles
- **Democracy First:** One identity = one base reputation.
- **Transparency:** Open-source, copyleft-licensed from inception.
- **Extensibility:** DSL-driven rules, easy to update without rewriting core code.
- **Decentralization:** Avoids central points of control or censorship.
