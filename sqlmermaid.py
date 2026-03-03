"""Generate Mermaid ER diagrams from SQLAlchemy databases.

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
"""

import argparse
import re
import tempfile
import urllib
import webbrowser
from collections import defaultdict
from pathlib import Path

import sqlalchemy as sa

__version__ = "1.0.0"


def get_mermaid(constr_or_meta: str | sa.MetaData) -> str:
    """Generate a Mermaid erDiagram string from a database or MetaData instance.

    Accepts a SQLAlchemy connection string (which triggers reflection including
    views) or a pre-populated MetaData. Raises TypeError for any other type.

    Example::

        >>> get_mermaid("sqlite:///:memory:")
        'erDiagram'
    """
    if isinstance(constr_or_meta, str):
        engine = sa.create_engine(constr_or_meta)
        meta = sa.MetaData()
        meta.reflect(bind=engine, views=True)
    elif isinstance(constr_or_meta, sa.MetaData):
        meta = constr_or_meta
    else:
        raise TypeError(
            "Expected `constr_or_meta` to be a `str` or `sa.MetaData` instance!\n"
            f"type(constr_or_meta) = {type(constr_or_meta)}"
        )

    nodes = [to_mermaid_node(table) for table in meta.tables.values()]

    edge_fstr = '"%s" ||--|{ "%s" : "%s"'
    edges = []
    for table_id, table in meta.tables.items():
        edge_dic = defaultdict(list)
        for fk in table.foreign_keys:
            col = fk.column
            target_col = fk.target_fullname.split(".")[-1]
            edge_dic[col.table.fullname].append((fk.parent.name, target_col))
        for target_table, colpairs in edge_dic.items():
            edge_label = "; ".join(f"{c1} -> {c2}" for c1, c2 in colpairs)
            edges.append(edge_fstr % (table_id, target_table, edge_label))
    return "\n  ".join(["erDiagram", *nodes, *edges])


def to_mermaid_node(table: sa.Table) -> str:
    """Render a single SQLAlchemy table as a Mermaid entity block.

    Columns are annotated with PK, FK, and index membership where applicable.
    Column type sizes are rewritten from TYPE(n) to TYPE-n for Mermaid
    compatibility (parentheses are not valid in entity definitions).
    """
    pks = {c.name for c in table.primary_key.columns}
    ind_dic = {i.name: [c.name for c in i.columns] for i in table.indexes}
    fks = {fk.parent.name for fk in table.foreign_keys}
    cols = []
    for col in table.columns:
        cn = col.name
        extra = "PK" if cn in pks else ("FK" if cn in fks else "")
        in_inds = [k for k, v in ind_dic.items() if cn in v]
        if in_inds:
            comm = f'"in index: {", ".join(in_inds)}"'
        else:
            comm = ""
        cols.append(" ".join(["   ", format_col_type(col), cn, extra, comm]))
    head = '"%s" {' % table.fullname
    return "    \n".join([head, *cols]) + "\n  }"


def format_col_type(col: sa.Column) -> str:
    """Format a column's type as a Mermaid-safe string.

    Rewrites parenthesised size specifiers so they are valid inside Mermaid
    entity definitions, e.g. VARCHAR(255) becomes VARCHAR-255 and
    NUMERIC(10, 2) becomes NUMERIC-10-2.
    """
    try:
        out = col.type.get_col_spec()
    except (AttributeError, NotImplementedError):
        out = str(col.type)
    return re.sub(
        r"\((\d+(?:,\s*\d+)*)\)",
        lambda m: "-" + re.sub(r",\s*", "-", m.groups()[0]),
        out,
    )


def to_file(constr: str, output_fp: str) -> None:
    """Write a schema diagram to a Markdown or HTML file.

    The output format is determined by the file extension: .md produces a
    fenced Mermaid code block, .html produces a standalone page rendered via
    the Mermaid CDN. Raises ValueError for unsupported extensions.
    """
    out_path = Path(output_fp)
    try:
        frame = frame_dic[out_path.suffix]
    except KeyError:
        raise ValueError(f"extension not in {list(frame_dic.keys())}")

    out_path.write_text(frame % get_mermaid(constr))


def open_in_browser(constr: str) -> None:
    """Open a schema diagram in the default web browser.

    Writes the diagram to a temporary HTML file and opens it. The file is not
    cleaned up automatically so the browser can load it after this returns.

    Example::

        >>> open_in_browser("sqlite:///:memory:")
    """
    output_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    to_file(constr, output_file.name)
    url = urllib.parse.urlunparse(("file", "", output_file.name, "", "", ""))
    webbrowser.open(url)


def main() -> None:
    """Command-line entry point for ``python -m sqlmermaid``.

    Prints to stdout by default; use -o/--output to write a file or
    --browser to open in the default browser.
    """
    parser = argparse.ArgumentParser(
        prog="sqlmermaid",
        description="Generate Mermaid ER diagrams from SQL databases.",
    )
    parser.add_argument("connection_string", help="SQLAlchemy connection string")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="write diagram to FILE (.md or .html)",
    )
    group.add_argument(
        "--browser",
        action="store_true",
        help="open diagram in the default browser",
    )
    args = parser.parse_args()

    if args.output:
        to_file(args.connection_string, args.output)
    elif args.browser:
        open_in_browser(args.connection_string)
    else:
        print(get_mermaid(args.connection_string))


html_frame = """
<html>
    <body>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({ startOnLoad: true });
        </script>

        <h1>EDR</h1>
        <div class="mermaid">
%s
        </div>
    </body>
</html>
"""


md_frame = """
```mermaid
%s
```

"""

frame_dic = {".html": html_frame, ".md": md_frame}

if __name__ == "__main__":
    main()
