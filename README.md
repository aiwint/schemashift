# schemashift

> CLI tool to detect and summarize breaking schema changes across Parquet and Arrow datasets.

---

## Installation

```bash
pip install schemashift
```

Or install from source:

```bash
git clone https://github.com/yourname/schemashift.git
cd schemashift && pip install -e .
```

---

## Usage

Compare two Parquet files and report breaking schema changes:

```bash
schemashift compare old_dataset.parquet new_dataset.parquet
```

Compare Arrow IPC files with detailed output:

```bash
schemashift compare schema_v1.arrow schema_v2.arrow --format json
```

**Example output:**

```
[BREAKING] Column 'user_id' type changed: int32 → string
[BREAKING] Column 'timestamp' removed
[INFO]     Column 'session_id' added (non-breaking)

2 breaking change(s) detected.
```

### Options

| Flag | Description |
|------|-------------|
| `--format` | Output format: `text` (default) or `json` |
| `--strict` | Treat added columns as breaking changes |
| `--quiet` | Only exit with non-zero code on breaking changes |

---

## Supported Formats

- Apache Parquet (`.parquet`)
- Apache Arrow IPC (`.arrow`, `.feather`)

---

## License

This project is licensed under the [MIT License](LICENSE).