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
    if network_type == "debtor->creditor":
        log.info("Extracting network type = {}".format(network_type))
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
    
    nodes_df.to_csv(nodes_tsv, encoding="utf-8", sep="\t", index=False)
    edges_df.to_csv(edges_tsv, encoding="utf-8", sep="\t", index=False)
    log.info("Finished!")
        

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
    administrators_df["type"] = "administrator"
    log.info("Extracted {} administrator records".format(len(administrators_df)))
    
    return administrators_df

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