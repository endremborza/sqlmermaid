# sqlmermaid

[![pypi](https://img.shields.io/pypi/v/sqlmermaid.svg)](https://pypi.org/project/sqlmermaid/)

Generate Mermaid ER diagrams from any SQLAlchemy-supported database — just pass a connection string.

```mermaid
erDiagram
  "complaints" {
     INTEGER about_dept FK
     INTEGER by_user FK
     DATETIME at_time
     VARCHAR-500 text "in index: comp_ind"
  }
  "departments" {
     INTEGER department_id PK
     VARCHAR-60 department_name
  }
  "user" {
     INTEGER user_id PK
     VARCHAR-16 user_name
     VARCHAR-60 email_address
     VARCHAR-50 nickname
  }
  "employees" {
     INTEGER employee_id PK
     VARCHAR-60 employee_name
     INTEGER employee_dept FK
  }
  "complaints" ||--|{ "user" : "by_user -> user_id"
  "complaints" ||--|{ "departments" : "about_dept -> department_id"
  "employees" ||--|{ "departments" : "employee_dept -> department_id"
```

## Installation

```
pip install sqlmermaid
```

## Usage

### Python API

```python
from sqlmermaid import get_mermaid, to_file, open_in_browser

# Mermaid diagram as a string
print(get_mermaid("sqlite:///mydb.db"))

# Write to a file
to_file("postgresql://user:pass@host/db", "schema.md")   # fenced Mermaid block
to_file("postgresql://user:pass@host/db", "schema.html") # standalone HTML page

# Open in browser
open_in_browser("sqlite:///mydb.db")
```

You can also pass a pre-populated `sqlalchemy.MetaData` object:

```python
import sqlalchemy as sa
from sqlmermaid import get_mermaid

meta = sa.MetaData()
meta.reflect(bind=engine)
print(get_mermaid(meta))
```

### Command line

```
python -m sqlmermaid <connection_string> [options]
```

| Option | Description |
|--------|-------------|
| _(none)_ | Print Mermaid diagram to stdout |
| `-o FILE` / `--output FILE` | Write diagram to `.md` or `.html` |
| `--browser` | Open diagram in the default browser |

```bash
# Print to stdout
python -m sqlmermaid sqlite:///mydb.db

# Write Markdown
python -m sqlmermaid sqlite:///mydb.db -o schema.md

# Open in browser
python -m sqlmermaid postgresql://user:pass@localhost/mydb --browser
```

## Diagram features

- Columns annotated with `PK` and `FK`
- Index membership noted in column comments
- Foreign key relationships rendered as labelled edges
- Column size specifiers rewritten for Mermaid compatibility (`VARCHAR(255)` → `VARCHAR-255`, `NUMERIC(10, 2)` → `NUMERIC-10-2`)
- Views included when reflecting from a connection string

## Output formats

| Extension | Description |
|-----------|-------------|
| `.md` | Fenced Mermaid code block |
| `.html` | Standalone page rendered via the Mermaid CDN |
