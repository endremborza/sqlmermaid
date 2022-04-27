"""Visualizing SQL databases"""

import re
import tempfile
import urllib
import webbrowser
from pathlib import Path

import sqlalchemy as sa

__version__ = "0.1.0"


def get_mermaid(constr):
    engine = sa.create_engine(constr)
    meta = sa.MetaData(bind=engine)
    sa.MetaData.reflect(meta)
    nodes = [to_mermaid_node(table) for table in meta.tables.values()]

    edge_fstr = '%s ||--|{ %s : "%s"'
    edges = []
    for table_id, table in meta.tables.items():
        for fk in table.foreign_keys:
            col = fk.column
            edges.append(edge_fstr % (table_id, col.table.fullname, fk.parent.name))
    return "\n  ".join(["erDiagram", *nodes, *edges])


def to_mermaid_node(table: sa.Table):
    pks = set([c.name for c in table.primary_key.columns])
    ind_dic = {i.name: [c.name for c in i.columns] for i in table.indexes}
    fks = set([fk.parent.name for fk in table.foreign_keys])
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
    head = table.fullname + " {"
    return "    \n".join([head, *cols]) + "\n  }"


def format_col_type(col):
    try:
        out = col.type.get_col_spec()
    except (AttributeError, NotImplementedError):
        out = str(col.type)
    return re.sub(r"\((\d+)\)", lambda m: "-" + m.groups()[0], out)


def to_file(constr: str, output_fp: str):
    """writes schema diagram to file

    markdown or html depending on file extension
    """
    out_path = Path(output_fp)
    try:
        frame = frame_dic[out_path.suffix]
    except KeyError:
        raise ValueError(f"extension not in {frame_dic.keys()}")

    out_path.write_text(frame % get_mermaid(constr))


def open_in_browser(constr):
    """opens schema diagram in the browser

    >>> open_in_browser("sqlite:///:memory:")
    """
    output_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    to_file(constr, output_file.name)
    url = urllib.parse.urlunparse(("file", "", output_file.name, "", "", ""))
    webbrowser.open(url)


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
