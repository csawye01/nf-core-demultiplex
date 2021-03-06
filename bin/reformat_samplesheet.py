#!/usr/bin/env python

import re
import pandas as pd
import argparse
import csv
import numpy as np
import sys

# need args for directory to put 10X samplesheet if applicable
argparser = argparse.ArgumentParser()
argparser.add_argument('--samplesheet', type=str)
ARGS = argparser.parse_args()

samplesheet = ARGS.samplesheet

# function to get idx of Data tag
data_tag_search = '[Data]'
data_index = 0
with open(samplesheet, 'r') as f:
    reader = csv.reader(f, delimiter=',')
    for idx, row in enumerate(reader):
        if data_tag_search in row:
            data_index = idx


# get all info above the [Data] tag
with open(samplesheet, 'r') as myfile:
    head = [next(myfile) for x in range(data_index)]

sample_pd = pd.read_csv(samplesheet, skiprows=range(0, data_index + 1))

# check samplesheet has all columns needed
if not set(['Lane', 'Sample_ID', 'index', 'index2', 'Sample_Project', 'ReferenceGenome', 'DataAnalysisType']).issubset(sample_pd.columns):
    sys.exit("The column headers in the samplesheet do not match the expected headings")

sample_pd = sample_pd.fillna('')
sample_pd['index'] = sample_pd['index'].astype('str')
sample_pd['index2'] = sample_pd['index2'].astype('str')

# ensure no leading or trailing whitespace
sample_pd['index'] = sample_pd['index'].str.strip()
sample_pd['index2'] = sample_pd['index2'].str.strip()

# remove rows and create new samplesheet with 10X samples
sc_list = ['10X-3prime']

# dictionary to map latin name with cell ranger genome ref name
cellranger_ref_genome_dict = {'Homo sapiens':'GRCh38', 'Mus musculus':'mm10', 'Danio rerio':'GRCz10',
                              'Gallus gallus':'Gallus_gallus', 'Drosophila melanogaster':'Drosophila_melanogaster'}

# create new csv for just 10X samples
cellranger_10X_df = sample_pd[sample_pd['DataAnalysisType'].isin(sc_list)].copy()
cellranger_idx_list_to_drop = cellranger_10X_df.index.values.tolist()
cellranger_10X_df['ReferenceGenome'] = cellranger_10X_df['ReferenceGenome'].map(cellranger_ref_genome_dict).fillna(cellranger_10X_df['ReferenceGenome'])

#combine 10X sample indexes
total_idx_to_drop = cellranger_idx_list_to_drop 
cellranger_needed = 'false'
if len(cellranger_10X_df) > 0:
    with open('tenX_samplesheet.tenx.csv', 'w+') as fp:
        fp.write('[Data]\n')
        cellranger_10X_df.to_csv(fp, index=False)
        fp.close()
    cellranger_needed = 'true'

reg = open(cellranger_needed + ".tenx.txt", "w")
reg.close()


# check there are no empty rows counted as strings
# checks if all columns are the same as first column indicating blanks counted as strings
results = list(sample_pd[sample_pd.eq(sample_pd.iloc[:, 0], axis=0).all(axis=1)].index.values.astype(int))
if results:
    total_idx_to_drop = total_idx_to_drop + results 

sample_pd.drop(sample_pd.index[total_idx_to_drop], inplace=True)

bcl2fastq = 'true'
if len(sample_pd) == 0 or sample_pd.empty:
    bcl2fastq = 'false'
    
bcl2fastq_needed = open(bcl2fastq + ".bcl2fastq.txt", "w")
bcl2fastq_needed.close()

# replace header info
with open('ReformattedSampleSheet.csv', 'w+') as f:
    for item in head:
        f.write(item)
    f.write('[Data]\n')
    sample_pd['Lane'] = sample_pd['Lane'].astype(int)
    sample_pd.to_csv(f, index=False)
    f.close()
