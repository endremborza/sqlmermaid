Multiple Foreign Keys
=====================

.. code:: ipython3

    from pathlib import Path
    
    import sqlalchemy as sa
    
    from sqlmermaid import get_mermaid, open_in_browser

.. code:: ipython3

    metadata_obj = sa.MetaData()

.. code:: ipython3

    user = sa.Table(
        "user",
        metadata_obj,
        sa.Column("user_name", sa.String(16), primary_key=True),
        sa.Column("email_address", sa.String(60), primary_key=True),
        sa.Column("nickname", sa.String(50), nullable=False),
    )

.. code:: ipython3

    user_buddy = sa.Table(
        "other",
        metadata_obj,
        sa.Column("num", sa.Integer),
        sa.Column("buddy_name", sa.String, sa.ForeignKey("user.user_name")),
        sa.Column("buddy_email", sa.String, sa.ForeignKey("user.email_address")),
    )

.. code:: ipython3

    db_file = Path("db2.sqlite")
    constr = f"sqlite:///{db_file}"
    engine = sa.create_engine(constr)
    metadata_obj.create_all(engine)
    
    # generates the raw mermaid string
    mermaid_str = get_mermaid(constr)

.. code:: ipython3

    # open_in_browser(constr)

.. code:: ipython3

    db_file.unlink()
