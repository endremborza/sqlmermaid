.. code:: ipython3

    import sqlalchemy as sa
    
    from sqlmermaid import get_mermaid
    
    
    metadata_obj = sa.MetaData()

.. code:: ipython3

    user = sa.Table(
        "user",
        metadata_obj,
        sa.Column("user_id", sa.Integer, primary_key=True),
        sa.Column("user_name", sa.String(16), nullable=False),
        sa.Column("email_address", sa.String(60)),
        sa.Column("nickname", sa.String(50), nullable=False),
    )

.. code:: ipython3

    departments = sa.Table(
        "departments",
        metadata_obj,
        sa.Column("department_id", sa.Integer, primary_key=True),
        sa.Column("department_name", sa.String(60), nullable=False),
    )

.. code:: ipython3

    employees = sa.Table(
        "employees",
        metadata_obj,
        sa.Column("employee_id", sa.Integer, primary_key=True),
        sa.Column("employee_name", sa.String(60), nullable=False),
        sa.Column("employee_dept", sa.Integer, sa.ForeignKey("departments.department_id")),
    )

.. code:: ipython3

    user_complaints = sa.Table(
        "complaints",
        metadata_obj,
        sa.Column("about_dept", sa.Integer, sa.ForeignKey("departments.department_id")),
        sa.Column("by_user", sa.Integer, sa.ForeignKey("user.user_id")),
        sa.Column("at_time", sa.DateTime),
        sa.Column("text", sa.String(500)),
        sa.Index("comp_ind", "text"),
    )

.. code:: ipython3

    constr = "sqlite:///db3.sqlite"  # "sqlite:///:memory:"
    engine = sa.create_engine(constr)
    metadata_obj.create_all(engine)
    
    print(get_mermaid(constr))
