from sqlalchemy import create_engine, MetaData
import os
import pandas as pd

ISIR_CONN_VAR = "ISIR_DB_CONNECTION_STRING"

def init_db_connection():
    
    if ISIR_CONN_VAR not in os.environ:
        raise Exception("%s not defined." % ISIR_CONN_VAR)
    engine = create_engine(os.environ[ISIR_CONN_VAR], convert_unicode=True)
    metadata = MetaData(bind=engine)
    return (engine, metadata)

engine, _ = init_db_connection()

def sql2df(sql_query, params={}):
    result = engine.execute(sql_query, params)
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df