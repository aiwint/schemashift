"""Read and extract schemas from Parquet and Arrow (IPC) files."""

from pathlib import Path
from typing import Union

import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.ipc as ipc


SUPPORTED_EXTENSIONS = {".parquet", ".arrow", ".feather"}


def read_schema(path: Union[str, Path]) -> pa.Schema:
    """Read and return the Arrow schema from a Parquet or Arrow file.

    Args:
        path: Path to the Parquet or Arrow/Feather file.

    Returns:
        A pyarrow.Schema representing the file's schema.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if suffix == ".parquet":
        return pq.read_schema(path)

    # .arrow / .feather — Arrow IPC format
    with pa.memory_map(str(path), "r") as source:
        try:
            reader = ipc.open_file(source)
        except pa.ArrowInvalid:
            reader = ipc.open_stream(source)
        return reader.schema_arrow
