from db import sql2df
from logging_setup import get_logger
import argparse
import pandas as pd
import datetime
import numpy as np
import re

log = get_logger("export_network")

TOP_N_CREDITORS = 100
MAX_DATE = datetime.date(2019, 1, 1)        

def export_network(network_type, nodes_tsv, edges_tsv):
    creditors_df = extract_creditors()
    creditor_ids = list(creditors_df.id)
    insolvencies_df = extract_insolvencies(creditor_ids)
    debtors_df = insolvencies2debtors(insolvencies_df)
    insolvency_end_dates_df = extract_insolvency_end_dates()

    nodes_df = pd.DataFrame([], columns=["id", "name", "node_type"])
    nodes_df = nodes_df.append(creditors_df).append(debtors_df)
    edges_df = pd.DataFrame([], columns=["source_id", "target_id", "edge_type", "start_date", "end_date"])

    log.info("Extracting network type = {}".format(network_type))
    if network_type == "debtor->creditor":
        log.info("Extracting debtor->creditor edges...")
        insolvency_creditor_edges_df = extract_insolvency_creditor_edges()
        insolvency_creditor_edges_df = insolvency_creditor_edges_df.merge(
            insolvency_end_dates_df, left_on="insolvency_id", right_on="insolvency_id", how="left"
        )

        debtor_creditor_edges_df = insolvency_creditor_edges_df\
            .merge(insolvencies_df[["insolvency_id", "debtor_id"]].drop_duplicates(),
                    on="insolvency_id")\
            [["debtor_id", "creditor_id", "start_date", "end_date"]]\
            .rename(columns={"debtor_id": "source_id", "creditor_id": "target_id"})
        debtor_creditor_edges_df["edge_type"] = "debtor_creditor"
        debtor_creditor_edges_df = debtor_creditor_edges_df[
            ["source_id", "target_id", "edge_type", "start_date", "end_date"]]
        edges_df = edges_df.append(debtor_creditor_edges_df)
        log.info("Extracted {} debtor->creditor edges".format(len(debtor_creditor_edges_df)))

    if network_type == "debtor->administrator->creditor":
        administrators_df = extract_administrators(creditor_ids)
        nodes_df = nodes_df.append(administrators_df)

        insolvency_administrator_edges_df = extract_insolvency_administrator_edges()
        
        debtor_administrator_edges_df = to_debtor_administrator_edges(insolvency_administrator_edges_df, insolvency_end_dates_df, insolvencies_df)
        administrator_creditor_edges_df = extract_administrator_creditor_edges(insolvency_end_dates_df, creditor_ids)
        edges_df = edges_df\
            .append(debtor_administrator_edges_df)\
            .append(administrator_creditor_edges_df)
    
    nodes_df = nodes_df[["id", "name", "node_type", "person_type", "region_id"]]
    nodes_df.to_csv(nodes_tsv, encoding="utf-8", sep="\t", index=False)

    edges_df = edges_df[["source_id", "target_id", "edge_type", "start_date", "end_date"]]
    edges_df.to_csv(edges_tsv, encoding="utf-8", sep="\t", index=False)
    log.info("Finished!")

def extract_administrator_creditor_edges(insolvency_end_dates_df, creditor_ids):
    log.info("Converting to administrator -> creditor edges...")
    administrator_creditor_edges_df = sql2df("""
        SELECT ft.insolvency_id, administrator_id, creditor_string_id, start_date::DATE, end_date::DATE
        FROM insolvencies_administrators_tab iat
             JOIN file_tab ft ON ft.insolvency_id = iat.insolvency_id
        WHERE ft.creditor_string_id IS NOT NULL 
              AND ft.creditor_string_id = ANY(%(creditor_ids)s)
    """, creditor_ids=creditor_ids).drop_duplicates()
    
    administrator_creditor_edges_df["administrator_id"] = administrator_creditor_edges_df["administrator_id"].apply(
        lambda id_: "adm_%d" % id_
    )
    administrator_creditor_edges_df = normalize_df_by_ins_id(administrator_creditor_edges_df)
    administrator_creditor_edges_df = administrator_creditor_edges_df.drop_duplicates()
    
    administrator_creditor_edges_df = administrator_creditor_edges_df\
        .merge(insolvency_end_dates_df, on="insolvency_id", how="left")
    administrator_creditor_edges_df["end_date"] = administrator_creditor_edges_df\
        .end_date_x.fillna(administrator_creditor_edges_df.end_date_y)
    
    administrator_creditor_edges_df = administrator_creditor_edges_df\
        .rename(columns={"administrator_id": "source_id", "creditor_string_id": "target_id"})\
        [["source_id", "target_id", "start_date", "end_date"]]
    administrator_creditor_edges_df["edge_type"] = "administrator_creditor"
    log.info("Extracted {} edge records".format(len(administrator_creditor_edges_df)))
    
    return administrator_creditor_edges_df
    
def to_debtor_administrator_edges(insolvency_administrator_edges_df, insolvency_end_dates_df, insolvencies_df):
    log.info("Converting to debtor -> administrator edges...")
    debtor_administrator_edges_df = insolvency_administrator_edges_df\
            .merge(insolvencies_df[["insolvency_id", "debtor_id"]].drop_duplicates(),
                   on="insolvency_id")
    debtor_administrator_edges_df = debtor_administrator_edges_df\
        .merge(insolvency_end_dates_df, on="insolvency_id", how="left")

    debtor_administrator_edges_df["end_date"] = debtor_administrator_edges_df\
        .end_date_x.fillna(debtor_administrator_edges_df.end_date_y)

    debtor_administrator_edges_df = debtor_administrator_edges_df\
        .rename(columns={"debtor_id": "source_id", "administrator_id": "target_id"})\
        [["source_id", "target_id", "start_date", "end_date"]]
    debtor_administrator_edges_df["edge_type"] = "debtor_administrator"
    log.info("Extracted {} edge records".format(len(debtor_administrator_edges_df)))
    return debtor_administrator_edges_df

def extract_insolvency_administrator_edges():
    log.info("Extracting insolvency -> administrator edges...")
    insolvency_administrator_edges_df = sql2df(
        "SELECT it.id AS insolvency_id, iat.administrator_id, start_date::DATE, end_date::DATE \
         FROM insolvencies_administrators_tab iat JOIN insolvency_tab it ON iat.insolvency_id=it.id"
    ).drop_duplicates()

    insolvency_administrator_edges_df["administrator_id"] = insolvency_administrator_edges_df["administrator_id"].apply(
        lambda id_: "adm_%d" % id_
    )
    insolvency_administrator_edges_df = normalize_df_by_ins_id(insolvency_administrator_edges_df)
    insolvency_administrator_edges_df = insolvency_administrator_edges_df.drop_duplicates()
    log.info("Extracted {} edge records".format(len(insolvency_administrator_edges_df)))
    return insolvency_administrator_edges_df

def insolvencies2debtors(insolvencies_df):
    log.info("Extracting debtors...")
    debtors_df = insolvencies_df.groupby("debtor_id")[["name", "person_type", "region_id"]]\
        .first().reset_index().rename(columns={"debtor_id": "id"})
    debtors_df["node_type"] = "debtor"
    log.info("Extracted {} debtor records".format(len(debtors_df)))
    return debtors_df[["id", "name", "node_type", "person_type", "region_id"]]

def extract_insolvency_creditor_edges():
    insolvency_creditor_edges_df = sql2df("""
        SELECT insolvency_id, creditor_string_id AS creditor_id, 
            proposal_timestamp::DATE AS start_date 
        FROM v_creditors_receivables 
            JOIN insolvency_tab it ON insolvency_id=it.id 
        WHERE creditor_string_id IS NOT NULL"""
    )
    insolvency_creditor_edges_df = normalize_df_by_ins_id(insolvency_creditor_edges_df)
    insolvency_creditor_edges_df = insolvency_creditor_edges_df.drop_duplicates()
    
    return insolvency_creditor_edges_df

def extract_insolvency_end_dates():
    insolvency_end_dates_df = sql2df("""
        SELECT insolvency_id, MAX(state_change_timestamp)::DATE AS end_date 
        FROM current_insolvency_states_tab cist 
            JOIN insolvency_states_types_tab istt ON cist.state = istt.id
        WHERE istt.text_identifier = 'ODSKRTNUTA' GROUP BY insolvency_id"""
    ) 
    insolvency_end_dates_df = normalize_df_by_ins_id(insolvency_end_dates_df)
    insolvency_end_dates_df = insolvency_end_dates_df.groupby("insolvency_id").max()
    
    return insolvency_end_dates_df

def extract_insolvencies(creditor_ids):
    log.info("Extracting insolvencies...")

    insolvencies_df = sql2df("""
        SELECT it3.id AS insolvency_id, it3.debtor_name AS name, it3.ico, 
                creditor_name2creditor_id(it3.debtor_name) AS string_id, it3.birth_number_hash_code,
                it3.person_type AS person_type, 
                it3.reference_number AS reference_number, it3.region_id AS region_id, 
                it3.proposal_timestamp::DATE AS date
            FROM insolvency_tab it3  
            JOIN (SELECT it.id 
                FROM insolvency_tab it 
                    JOIN v_creditors_receivables ft2 ON it.id=ft2.insolvency_id 
                WHERE ft2.creditor_string_id is not null 
                    AND ft2.creditor_string_id = ANY(%(creditor_ids)s) 
                GROUP BY it.id) as insolvencies 
            ON it3.id=insolvencies.id
        """, creditor_ids=creditor_ids
    ).drop_duplicates()

    insolvencies_df = insolvencies_df[insolvencies_df["date"] < MAX_DATE].copy()
    insolvencies_df = normalize_df_by_ins_id(insolvencies_df)
    insolvencies_df = insolvencies_df.groupby("insolvency_id").first().reset_index()

    insolvencies_df["debtor_id"] = insolvencies_df.ico\
        .apply(lambda i: None if pd.isnull(i) else int(i))\
        .fillna(insolvencies_df.birth_number_hash_code\
                           .apply(lambda n: None if pd.isnull(n) else int(n)))\
        .fillna(insolvencies_df.string_id)
    assert insolvencies_df.debtor_id.isna().sum() == 0
    log.info("Extracted {} insolvency records".format(len(insolvencies_df)))

    return insolvencies_df

def extract_administrators(creditor_ids):
    log.info("Extracting administrators...")
    administrators_df = sql2df("""
        SELECT at.id AS id, at.name AS name 
        FROM administrators_tab at 
        JOIN insolvencies_administrators_tab iat ON iat.administrator_id=at.id 
        JOIN (SELECT it.id 
            FROM insolvency_tab it 
                JOIN v_creditors_receivables ft2 ON it.id=ft2.insolvency_id 
            WHERE ft2.creditor_string_id is not null 
                AND ft2.creditor_string_id = ANY(%(creditor_ids)s) 
            GROUP BY it.id) as its 
        ON iat.insolvency_id=its.id 
        GROUP BY at.id, at.name""", creditor_ids=creditor_ids
    ).drop_duplicates()
    administrators_df["id"] = administrators_df["id"].apply(lambda id_: "adm_%d" % id_)
    administrators_df["node_type"] = "administrator"
    log.info("Extracted {} administrator records".format(len(administrators_df)))
    
    return administrators_df[["id", "name", "node_type"]]

def extract_creditors():
    log.info("Extracting creditors...")
    creditor_df = sql2df(
        "SELECT creditor_string_id AS id, max(creditor) as name, count(*) as count  \
        FROM v_creditors_receivables ft \
        GROUP BY creditor_string_id \
        ORDER BY count DESC \
        LIMIT 100"
    ).drop_duplicates().drop(labels=["count"], axis=1)
    creditor_df["node_type"] = "creditor"
    log.info("Extracted {} creditor records".format(len(creditor_df)))
    return creditor_df[["id", "name", "node_type"]]

def normalize_ins_id(iid):
    return iid.split("ins")[1]

def normalize_df_by_ins_id(df):
    df.insolvency_id = df.insolvency_id.apply(normalize_ins_id)
    df = df[
        df.insolvency_id.apply(lambda iid: re.match("^[0-9]+/[0-9]{4}$", iid) is not None)
    ]
    return df.copy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--network_type", required=True, help="Possible values: debtor->creditor|debtor->administrator->creditor")
    parser.add_argument("--nodes_tsv", required=True)
    parser.add_argument("--edges_tsv", required=True)
    args = parser.parse_args()

    if args.network_type not in ["debtor->creditor", "debtor->administrator->creditor"]:
        raise Exception("Invalid argument!")

    export_network(args.network_type, args.nodes_tsv, args.edges_tsv)