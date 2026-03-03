# sqlmermaid

Generate Mermaid ER diagrams from SQLAlchemy databases.

Reflects tables, columns, primary keys, foreign keys, and indexes from any
SQLAlchemy-supported database and renders them as a Mermaid ``erDiagram``
block suitable for embedding in Markdown files or viewing in a browser.

Typical usage::

    from sqlmermaid import get_mermaid, to_file, open_in_browser

    print(get_mermaid("sqlite:///mydb.db"))
    to_file("postgresql://user:pass@host/db", "schema.md")
    open_in_browser("sqlite:///mydb.db")

Command-line usage::

    python -m sqlmermaid sqlite:///mydb.db
    python -m sqlmermaid sqlite:///mydb.db -o schema.md
    python -m sqlmermaid sqlite:///mydb.db --browser

## `format_col_type(col: sqlalchemy.sql.schema.Column) -> str`
Format a column's type as a Mermaid-safe string.

    Rewrites parenthesised size specifiers so they are valid inside Mermaid
    entity definitions, e.g. VARCHAR(255) becomes VARCHAR-255 and
    NUMERIC(10, 2) becomes NUMERIC-10-2.

## `get_mermaid(constr_or_meta: str | sqlalchemy.sql.schema.MetaData) -> str`
Generate a Mermaid erDiagram string from a database or MetaData instance.

    Accepts a SQLAlchemy connection string (which triggers reflection including
    views) or a pre-populated MetaData. Raises TypeError for any other type.

    Example::

        >>> get_mermaid("sqlite:///:memory:")
        'erDiagram'

## `main() -> None`
Command-line entry point for ``python -m sqlmermaid``.

    Prints to stdout by default; use -o/--output to write a file or
    --browser to open in the default browser.

## `open_in_browser(constr: str) -> None`
Open a schema diagram in the default web browser.

    Writes the diagram to a temporary HTML file and opens it. The file is not
    cleaned up automatically so the browser can load it after this returns.

    Example::

        >>> open_in_browser("sqlite:///:memory:")

## `to_file(constr: str, output_fp: str) -> None`
Write a schema diagram to a Markdown or HTML file.

    The output format is determined by the file extension: .md produces a
    fenced Mermaid code block, .html produces a standalone page rendered via
    the Mermaid CDN. Raises ValueError for unsupported extensions.

## `to_mermaid_node(table: sqlalchemy.sql.schema.Table) -> str`
Render a single SQLAlchemy table as a Mermaid entity block.

    Columns are annotated with PK, FK, and index membership where applicable.
    Column type sizes are rewritten from TYPE(n) to TYPE-n for Mermaid
    compatibility (parentheses are not valid in entity definitions).
