import pandas as pd
import time
import psycopg2
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

# Connecting to the database via an SSH tunnel

server = SSHTunnelForwarder(('isir.zviri.cz', 22), ssh_private_key="/Users/peterzvirinsky/.ssh/id_rsa",
         ssh_username="root", remote_bind_address=('localhost', 5432))
server.start()

time.sleep(1)

db_string = 'postgresql://developer123:5AWi7e1l8JKE@localhost:{}/isir_prod_db'\
    .format(server.local_bind_port)

db_engine = create_engine(db_string)

def sql2df(sql_query, **sql_params):
    result = db_engine.execute(sql_query, **sql_params)
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df