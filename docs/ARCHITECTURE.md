# Architecture

```text
React editor / GitHub Pages
  -> browser project model
  -> optional FastAPI backend
  -> Python project schema
  -> editor operations
  -> safe patch application
  -> C export
  -> PVSnesLib runtime target
  -> .sfc artifact
```

## Modes

### Online demo mode

Static frontend only. Loads `web/public/examples/hello-human.snesproj`, edits in memory, and downloads `.snesproj`.

### Local backend mode

Runs Python/FastAPI locally. Supports validation, patching, C export, and ROM artifact generation.

## Compiler boundary

The compiler emits readable C stubs. This deliberately avoids the GB/GBA assembler trap: every platform backend should own its own runtime and codegen boundary.
