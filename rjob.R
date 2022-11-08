#!/usr/bin/env Rscript


library(readr)
library(aws.s3)

args <- commandArgs(trailingOnly = TRUE)


Sys.setenv("AWS_ACCESS_KEY_ID" = args[1],
           "AWS_SECRET_ACCESS_KEY" = args[2],
           "AWS_DEFAULT_REGION" = "us-east-2")

read <- read_csv('https://data.cityofchicago.org/api/views/bbt9-ihrm/rows.csv?accessType=DOWNLOAD')

read['MODDED'] = read['WARD'] * read['DATES']

s3write_using(read, FUN = write.csv,
              bucket = args[3],
              object = "RJOB.csv")