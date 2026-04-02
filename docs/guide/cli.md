# CLI Reference

The `speclib` command-line tool provides batch operations for ingestion, search, export, and serving.

## Commands

### `speclib ingest`

Ingest spectra from an upstream source.

```bash
speclib ingest <source> --config <path>
```

| Argument | Description |
|----------|-------------|
| `source` | Adapter name: `usgs`, `ecostress`, `aster`, `emit` |
| `--config` | Path to YAML configuration file |

### `speclib search`

Search the library catalog.

```bash
speclib search <query> [--category <category>]
```

| Argument | Description |
|----------|-------------|
| `query` | Search string (name, material, description) |
| `--category` | Filter by category: `MINERAL`, `VEGETATION`, `SOIL`, `MANMADE`, `KY_INVASIVE` |

### `speclib export`

Export a spectrum to a target format.

```bash
speclib export <spectrum_id> --format <format> --output <path>
```

| Argument | Description |
|----------|-------------|
| `spectrum_id` | Unique spectrum identifier |
| `--format` | Output format: `esl`, `sli`, `specpr`, `ascii`, `json` |
| `--output` | Output file path |

### `speclib resample`

Resample a spectrum to a target sensor.

```bash
speclib resample <spectrum_id> --sensor <sensor> --output <path>
```

### `speclib build`

Generate static web viewer files from the archive.

```bash
speclib build [--output <dir>]
```

### `speclib serve`

Start the FastAPI development server.

```bash
speclib serve [--host <host>] [--port <port>]
```
