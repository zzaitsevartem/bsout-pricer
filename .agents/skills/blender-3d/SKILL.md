---
name: blender-3d
description: Create, edit, and export Blender 3D assets for BScout, especially models based on supplied photo references and optimized for the website.
---

# Blender 3D for BScout

Inspect the supplied references and clarify only details that materially affect the model. Separate visible evidence from inferred geometry; a single photo cannot establish hidden surfaces. Compare proportions, silhouette, materials and distinctive details against the references from several views, and iterate with rendered previews.

Use the Blender MCP tools when available. The Blender application and its MCP add-on must be running; inspect the existing scene before changing it. Preserve existing work and save an editable `.blend` source alongside or in the location requested for the deliverable. Do not overwrite unrelated scenes or assets. Do not upload reference images or assets to external services without the user's authorization.

For website assets, inspect the existing implementation and its asset conventions before integration. Export a self-contained GLB when appropriate, preserve required animation and node names, and balance visual fidelity against geometry, texture size, download weight and runtime performance. Check the exported model by reopening it and, when integrated, verify it in the browser at relevant viewport sizes, including loading and fallback behavior. Report what was checked and any limitations or inferred details.
