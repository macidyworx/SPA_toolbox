# SORT PHASE 2

## Description
This document is for listing phase 2 changes and additions

### YAML validation
Figure out a practical way to validate and check the YAML formatting. Posibly a YAML validation helper that can be ran after any adds or manual edits.

### Configurable Sorting Strategies
Support sorting files by multiple dimensions (test type, variant, group, area) instead of only by test type.

#### Design: Default Sort Strategy Per Test Type

Each test type in `test_identifiers.yaml` defines its default sort strategy using a path template:

```yaml
PAT:
  priority: 1
  folder: "FolderName"
  group: "Assessment"
  area: "PatArea"
  variant: "online"                    # NEW: Variant/format attribute
  sort_strategy: "{group}/{variant}"   # NEW: Default strategy — e.g., "Assessment/online"
  SWAPPER_FILE: "..."
  ...

PAT_Template:
  priority: 2
  folder: "FolderName"
  group: "Assessment"
  area: "PatArea"
  variant: "template"
  sort_strategy: "{group}/{variant}"   # e.g., "Assessment/template"
  ...
```

#### Available Template Variables
- `{type}` — Test type name (PAT, SSSR, etc.)
- `{group}` — Group name (from config)
- `{variant}` — Variant name (from config)
- `{area}` — Area name (from config)
- `{folder}` — Folder name (from config, for backwards compatibility)

#### Default Behavior
- If `sort_strategy` not specified: fall back to `{folder}` (preserves current behavior)
- Runtime parameter can override: `sort_files(input_folder, override_strategy="{type}")`

#### Implementation Tasks
- [ ] Add `variant` and `sort_strategy` fields to test_identifiers.yaml schema
- [ ] Update File_Identifier to extract these fields
- [ ] Implement path template resolution in sort_files()
- [ ] Add schema validation for template variables
- [ ] Update YAML validation helper to check valid template syntax
- [ ] Add tests: different strategies produce correct folder structure
- [ ] Document examples: by-type, by-variant, by-group, custom overrides