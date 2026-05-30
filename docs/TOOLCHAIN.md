# Toolchain

The 1.0.0 repository does not require PVSnesLib for tests or the web demo.

For real playable SNES ROMs, the next runtime milestone should integrate PVSnesLib or an equivalent SNES homebrew C/ASM toolchain.

Until then:

```bash
snes-studio make:rom examples/hello-human/project.snesproj build/hello-human.sfc --skip-build
```

creates a placeholder artifact for CI/release workflow testing.
