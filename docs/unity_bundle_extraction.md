# Unity Asset Bundle Extraction - Research & Implementation Notes

## Summary

TTS mods use Unity Asset Bundles (`.unity3d` files) for 3D components like
table legs, custom models, particle effects, and sometimes game content
(program cards, gear tokens, etc.). These were previously marked as a "known
gap" in the toolchain.

**Solution**: Use [UnityPy](https://github.com/K0lb3/UnityPy) (Python, MIT
license, 1,245 stars) to extract textures directly.

## Unity Asset Bundle Format

- **Magic**: `UnityFS\0` (modern format)
- **Version**: 6 (for files built with Unity 5.6.2f1, which TTS uses)
- **Compression**: LZMA or LZ4/LZ4HC
- **Structure**: Header → Block info → Directory → CAB entries → Serialized files → Objects

Each bundle contains serialized Unity objects:
| Type | Description | Printable? |
|------|-------------|------------|
| Texture2D | Diffuse, normal, AO, metallic maps | Only diffuse/albedo |
| Sprite | 2D sprite images | Yes |
| Mesh | 3D geometry | No |
| Material | Shader parameters + texture refs | No |
| GameObject | Scene hierarchy nodes | No |
| AudioClip | Sound effects | No |
| AnimationClip | Animations | No |
| ParticleSystem | Particle effects | No |

## Filtering Strategy

Not all Texture2D objects are printable. PBR (physically based rendering)
maps are used for 3D lighting and are visually meaningless when printed:

**Skip patterns** (suffix matching):
- `_n`, `_normal`, `_norm` — normal maps (blue-purple tinted)
- `_metallic`, `MetallicSmoothness` — metallic/smoothness maps
- `_ao`, `_occlusion` — ambient occlusion maps
- `_height` — height/displacement maps
- `_roughness`, `_specular`, `_emission`, `_mask`

Also skip textures smaller than 4x4 pixels (placeholders/defaults).

## Testing Results

Across 87 bundles from 4 mods (Ada, Rurik, Captain Sonar, MLEM):
- Total objects found: 2,104
- Texture2D objects: 167
- After filtering: 122 printable textures
- Zero extraction errors
- All images verified valid

## Tools Evaluated

| Tool | Type | Stars | Verdict |
|------|------|-------|---------|
| **UnityPy** | Python lib | 1,245 | **CHOSEN** — pip install, PIL Images, active |
| UABE | C++ GUI | 4,100 | Archived, Windows-only |
| UABEA | C# GUI | 2,100 | GUI-only, no CLI/API |
| AssetRipper | C# web GUI | 7,000 | .NET dependency, no batch CLI |
| UnityPack | Python lib | 747 | Dead since 2020 |
| asset-bundle-analyzer | Python | 233 | Deprecated, analysis only |

## Integration

New files:
- `src/extract_bundle_textures.py` — extraction logic
- `bin/tts-extract-bundles` — CLI wrapper
- `tests/test_bundle_extraction.py` — 7 unit tests

Output: `bundle_texture_metadata.json` (same format as `model_texture_metadata.json`)
reuses `tts-generate-model-textures-pdf` for PDF generation.

Pipeline step added to `bin/tts-mod` between model extraction and PDF generation.
