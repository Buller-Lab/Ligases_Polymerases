import os
import pandas as pd
import subprocess

input_fasta = "isatin_hydrolase_seeds.fasta"
project_name = "isatin_hydrolase_NR"
database = "/home/stcg/Documents/mmseqs_dbs/NR"
output_dir = project_name

path = output_dir

isExist = os.path.exists(path)
if not isExist:
    os.makedirs(path)
    print("The new project directory was created!")
else:
    print("This directory already exists, overwriting the old directory!")

subprocess.run(f"mmseqs easy-search {input_fasta} {database} {output_dir}/alnRes.m8 tmp --format-output 'target,tseq,pident,tlen,taxid,taxname,taxlineage' --min-seq-id 0.3 --split-memory-limit 60G", shell=True)

hits=pd.read_csv(f'{output_dir}/alnRes.m8', sep='	',header=None)
hits.columns = ['ID','Sequence','SeqID_Seed','Length','TaxID','Organism','TaxInfo']
for index, row in hits.iterrows():
    with open(f'{output_dir}/hits.fasta', 'a') as hits_fasta:
        if index==0:
            hits_fasta.truncate(0)
        hits_fasta.write('>'+row['ID']+'\n')
        hits_fasta.write(row['Sequence']+'\n')
hits_fasta=f"{output_dir}/hits.fasta"

subprocess.run(f"mmseqs easy-linclust {output_dir}/hits.fasta {database} {output_dir}/clusterRes_60 tmp --min-seq-id 0.6 -c 0.8 --cov-mode 0", shell=True)

with open(f'{output_dir}/clusterRes_60_cluster.tsv', 'r') as original: data = original.read()
with open(f'{output_dir}/clusterRes_60_cluster.tsv', 'w') as modified: modified.write("Cluster	ID\n" + data)
       
with open(f'{output_dir}/alnRes.m8', 'r') as original: data = original.read()
with open(f'{output_dir}/alnRes.m8', 'w') as modified: modified.write("ID	Sequence	SeqID_Seed	Length	TaxID	Organism	TaxInfo\n" + data)


cluster_60=pd.read_csv(f'{output_dir}/clusterRes_60_cluster.tsv',sep='	')
for index, row in cluster_60.iterrows():
    if row['Cluster'] == row['ID']:
        if list(cluster_60['Cluster']).count(str(row['Cluster'])) > 1:
            cluster_60=cluster_60.drop([index])
        elif row['Cluster'] == "Cluster":
            cluster_60=cluster_60.drop([index])
cluster_60.to_csv(f'{output_dir}/clusterRes_60_cluster.tsv',sep='	',index=None)

