import subprocess
import sys

import pytest
import sqlalchemy as sa

from sqlmermaid import format_col_type, get_mermaid, open_in_browser, to_file, to_mermaid_node


@pytest.fixture
def meta() -> sa.MetaData:
    m = sa.MetaData()
    sa.Table(
        "users",
        m,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50)),
        sa.Column("email", sa.String(100)),
    )
    sa.Table(
        "posts",
        m,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(200)),
    )
    return m


class TestGetMermaid:
    def test_from_constring(self):
        result = get_mermaid("sqlite:///:memory:")
        assert result.startswith("erDiagram")

    def test_from_metadata(self, meta):
        result = get_mermaid(meta)
        assert result.startswith("erDiagram")
        assert "users" in result
        assert "posts" in result

    def test_pk_fk_annotated(self, meta):
        result = get_mermaid(meta)
        assert " PK" in result
        assert " FK" in result

    def test_edge_rendered(self, meta):
        result = get_mermaid(meta)
        edge_lines = [ln for ln in result.splitlines() if "||--|{" in ln]
        assert any("users" in ln for ln in edge_lines)

    def test_edge_label_contains_column_name(self, meta):
        result = get_mermaid(meta)
        assert "user_id" in result

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            get_mermaid(42)


class TestFormatColType:
    def test_varchar_parens_replaced(self):
        col = sa.Column("x", sa.String(255))
        sa.Table("t", sa.MetaData(), col)
        result = format_col_type(col)
        assert "(" not in result
        assert "-255" in result

    def test_integer_no_parens(self):
        col = sa.Column("x", sa.Integer)
        sa.Table("t", sa.MetaData(), col)
        result = format_col_type(col)
        assert "(" not in result
        assert result

    def test_multiple_size_specs_replaced(self):
        # NUMERIC(10, 2) -> NUMERIC-10-2
        col = sa.Column("x", sa.Numeric(10, 2))
        sa.Table("t", sa.MetaData(), col)
        result = format_col_type(col)
        assert "(" not in result


class TestToMermaidNode:
    def test_contains_table_name(self, meta):
        node = to_mermaid_node(meta.tables["users"])
        assert '"users"' in node

    def test_pk_annotated(self, meta):
        node = to_mermaid_node(meta.tables["users"])
        assert "PK" in node

    def test_fk_annotated(self, meta):
        node = to_mermaid_node(meta.tables["posts"])
        assert "FK" in node

    def test_braces(self, meta):
        node = to_mermaid_node(meta.tables["users"])
        assert "{" in node and "}" in node

    def test_index_noted(self):
        m = sa.MetaData()
        t = sa.Table(
            "items",
            m,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("sku", sa.String(32)),
        )
        sa.Index("sku_idx", t.c.sku)
        node = to_mermaid_node(t)
        assert "sku_idx" in node


class TestToFile:
    def test_md_output(self, tmp_path):
        out = tmp_path / "schema.md"
        to_file("sqlite:///:memory:", str(out))
        content = out.read_text()
        assert "erDiagram" in content
        assert "```mermaid" in content

    def test_html_output(self, tmp_path):
        out = tmp_path / "schema.html"
        to_file("sqlite:///:memory:", str(out))
        content = out.read_text()
        assert "erDiagram" in content
        assert "<html>" in content

    def test_invalid_extension_raises(self, tmp_path):
        with pytest.raises(ValueError):
            to_file("sqlite:///:memory:", str(tmp_path / "schema.txt"))


class TestOpenInBrowser:
    def test_opens_file_url(self, monkeypatch):
        opened = []
        monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
        open_in_browser("sqlite:///:memory:")
        assert len(opened) == 1
        assert opened[0].startswith("file://")

    def test_temp_file_is_html(self, monkeypatch, tmp_path):
        captured = []
        monkeypatch.setattr("webbrowser.open", lambda url: captured.append(url))
        open_in_browser("sqlite:///:memory:")
        path = captured[0].replace("file://", "")
        assert path.endswith(".html")


class TestMain:
    def test_stdout(self):
        result = subprocess.run(
            [sys.executable, "-m", "sqlmermaid", "sqlite:///:memory:"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "erDiagram" in result.stdout

    def test_output_md_file(self, tmp_path):
        out = tmp_path / "schema.md"
        result = subprocess.run(
            [sys.executable, "-m", "sqlmermaid", "sqlite:///:memory:", "-o", str(out)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out.exists()
        assert "erDiagram" in out.read_text()

    def test_output_html_file(self, tmp_path):
        out = tmp_path / "schema.html"
        result = subprocess.run(
            [sys.executable, "-m", "sqlmermaid", "sqlite:///:memory:", "-o", str(out)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "<html>" in out.read_text()

    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "sqlmermaid", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "connection_string" in result.stdout

    def test_browser(self, monkeypatch):
        from sqlmermaid import main

        opened = []
        monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
        monkeypatch.setattr(
            "sys.argv", ["sqlmermaid", "sqlite:///:memory:", "--browser"]
        )
        main()
        assert len(opened) == 1

    def test_main_stdout_direct(self, monkeypatch, capsys):
        from sqlmermaid import main

        monkeypatch.setattr("sys.argv", ["sqlmermaid", "sqlite:///:memory:"])
        main()
        assert "erDiagram" in capsys.readouterr().out

    def test_main_output_file_direct(self, monkeypatch, tmp_path):
        from sqlmermaid import main

        out = tmp_path / "schema.md"
        monkeypatch.setattr(
            "sys.argv", ["sqlmermaid", "sqlite:///:memory:", "-o", str(out)]
        )
        main()
        assert "erDiagram" in out.read_text()
