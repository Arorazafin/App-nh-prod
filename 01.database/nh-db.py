

import pandas as pd
import numpy as np
import math

import argparse


from sqlalchemy import create_engine
import psycopg2
from collections import defaultdict

import sys


# env mngt
import os
from dotenv import load_dotenv 
load_dotenv()

import time
import datetime

import re


class dbNH(object):

    def __init__(self):
        colsSouscripteur = ['Code souscripteur', 'souscripteur','Adresse Ass',
                                   'Tel Ass','Mail Ass'
        ]
        idSouscripteur='Code souscripteur'

        
        colsPolice = ['Num police', 'Code souscripteur','Code branche','Code catégorie',
                      'Type avenant',  'Date effet police', 'Date échéance police',
        ]
        idPolice = 'Num police'

        ColsEtatQuittance = ['idEtat_quittance','Num quittance','Type mouvement','date_extraction', 'Num police',
                        'Date effet quittance','Date échéance quittance','Prime totale quittance', 
                        'Date comptabilisation','Date Encaiss quittance','Montant Encaissé quittance','Réf Encaissement','Etat Quittance',
                        'etat_police' ]
        idEtat_quittance='idEtat_quittance'
        
        colsBranche =['Code branche', 'Libellé branche'
        ]
        idAssuance_branche = 'Code branche'

        colsCategorie =['Code catégorie', 'Libellé catégorie'
        ]
        idAsssurance_categorie = 'Code catégorie'

        colsOrass = ['Type mouvement',
                        'Num quittance',
                        'Type quittance',
                        'Code branche',
                        'Libellé branche',
                        'Code catégorie',
                        'Libellé catégorie',
                        'Code type intermédiaire',
                        'Libellé type intermédiaire',
                        'Code intermédiaire',
                        'intermédiaire',
                        'Num police',
                        'Num avenant',
                        'Type avenant',
                        'Option Couverture',
                        'Référence police',
                        'Code souscripteur',
                        'souscripteur',
                        'Adresse Ass',
                        'Tel Ass',
                        'Mail Ass',
                        'Date effet police',
                        'Date échéance police',
                        'Date effet quittance',
                        'Date échéance quittance',
                        'Durée police',
                        'Unite durée police',
                        'Date emission',
                        'Date comptabilisation',
                        'Prime totale quittance',
                        'Prime nette quittance',
                        'Taux part coassurance',
                        'Prime nette garantie',
                        'Prime Nette garantie Cie',
                        'Prime Nette garantie coass',
                        'Accessoire/CP ',
                        'Taxes et Fonds',
                        'TE',
                        'TACAVA',
                        'TVA',
                        'Frais Gestion',
                        'Sans_TG',
                        'Commission',
                        'Total SMP',
                        'Total Capital',
                        'Total Capitaux Garantie',
                        'Montant Encaissé quittance',
                        'Date Encaiss quittance',
                        'Réf Encaissement',
                        'Etat Quittance',
                        'Bénéficiaires'
        ]

        idOrass = 'Num quittance'

        self.tables = dict()
        self.tables = { 'souscripteur' : [colsSouscripteur,idSouscripteur],
                        'police': [colsPolice, idPolice],
                        'etat_quittance': [ColsEtatQuittance,idEtat_quittance],
                        'assurance_branche':[colsBranche,idAssuance_branche],
                        'assurance_categorie': [colsCategorie,idAsssurance_categorie],
                       # 'orass' :[colsOrass,idOrass]

        }  

        self.colsdate = ['Date effet police',
            'Date échéance police',
            'Date effet quittance',
            'Date échéance quittance',
            'Date emission',
            'Date comptabilisation', 
            'Date Encaiss quittance'
        ]

        self.colsSage= ['N°ASSURE',
            'PIECE', 
            'N°POLICE',  
            'LIBELLE',        
            'OPE',       
            'TYPE_OPE',
            'EFFET', 
            'ECHEANCE',    
            'DEBIT',   
            'CREDIT',     
            'RGLT'
        ] 
    

        self.dt_orassExtraction = datetime.date(2000,12,1)
        self.dt_sageExtraction = datetime.date(2000,12,1)
        self.df = pd.DataFrame()  # pandas dataframe of loan data
        self.df_fromPostegres = pd.DataFrame()
        self.df_new_table = pd.DataFrame()
        self.df_diff = pd.DataFrame()
        
        self.sql = defaultdict()  # info for connecting to postgres db
        self.sql_engine = None  # used with sqlalchemy
        self.query = ''
        self.queryRes =''

    def import_json(self, files):
        '''
        import json file
        '''
        #with open(files) as f:
        #    dic = json.load(f)
        #self.df = pd.DataFrame(dic)

    def import_csv(self, files):
        '''
        import csv file
        '''
        self.df = pd.read_csv(files, sep=',')

    def import_xls(self, files):
        '''
        import xls file
        '''
        #try:
        self.df = pd.read_excel(files)
        #except:
        
        

    def transform_dates(self):
        '''
        '''
        
        df1 = self.df.copy()
        col_date = self.colsdate
        for d in col_date:
            df1[d] = pd.to_datetime(df1[d], format='%d/%m/%Y', errors='coerce')

        self.df = df1.copy()


   

    def transform_df_orass(self):
        '''
        Transforms the dataframe from NEW orass excel
        '''

        if self.df.columns[0]=='Type mouvement':
            #self.dt_orassExtraction = dt_orass
            self.df['dateExtraction'] = self.dt_orassExtraction
        else:
            col_date = self.df.columns[0]
            col_split = re.split(r'\s',col_date)
            dt_txt = col_split[len(col_split)-1].replace("'","")
            dt_orass = datetime.datetime.strptime(dt_txt,'%d/%m/%Y')
            self.dt_orassExtraction = dt_orass
       
            col=  self.df.loc[1,].to_numpy()
            self.df.columns = col
            self.df.drop([0,1], inplace = True)
            self.df['dateExtraction'] = dt_orass


     
    def setup_sql(self):

        '''
        sets up sql connection for exporting and loading from sql
        must be run before export_to_sql, load_from_sql, or merge_db
        '''
 
        engstr = 'postgresql://%s:%s@%s:%s/%s' % (self.sql['user'], self.sql['pw'], self.sql['host'], self.sql['port'], self.sql['db'])
        self.sql_engine = create_engine(engstr)
       

    def run_query(self):
        '''
        Executes self.query. Used by export_to_sql
        '''
        conn = psycopg2.connect(dbname=self.sql['db'], user=self.sql['user'],
                                host=self.sql['host'], password=self.sql['pw'])
        c = conn.cursor()
        c.execute(self.query)
        conn.commit()
        conn.close()
        self.query = ''

    def run_query_printRes(self):
        '''
        Executes self.query. Used by export_to_sql
        '''
        conn = psycopg2.connect(dbname=self.sql['db'], user=self.sql['user'],
                                host=self.sql['host'], password=self.sql['pw'])
        

        c = conn.cursor()
        c.execute(self.query)
        results = c.fetchall()
        conn.commit()
        conn.close()
        self.queryRes = results
        self.query = ''

    def run_query_del(self):
        '''
        Executes self.query. Used by export_to_sql
        '''
        conn = psycopg2.connect(dbname=self.sql['db'], user=self.sql['user'],
                                host=self.sql['host'], password=self.sql['pw'])
        

        c = conn.cursor()
        c.execute(self.query)
        conn.commit()
        conn.close()
        self.queryRes = "Delete done"
        self.query = ''
        
    

    
    def export_to_sql_initTables_new(self, table):
    
        dfx = self.df.copy()
        #dfx = pd.concat([self.df_fromPostegres,dfx],axis =0)       
        #dfx.reset_index(drop = True, inplace = True)
        dfx.to_sql(table, self.sql_engine, if_exists='replace', index = False)
        #self.df = dfx.copy()




    def read_table(self,table):
        try: 
            dfx  = pd.read_sql("SELECT * FROM "+ table, self.sql_engine)
            self.df_fromPostegres = dfx.copy()
        except:
            self.df_fromPostegres = pd.DataFrame()

    def query_create_table(self,table):
        self.query = 'CREATE TABLE' + table + '('+ self.tables[table][0]+')'




    def run_importXlsFile_nh(self, filename, name_table):
        '''
        Imports, transforms, and loads loan data into sql.
        '''

        t_start = time.perf_counter()

        xfile = '01.database/data-excel/%s' % filename
        print('file found: ',xfile)
        try:

            self.import_xls(files=xfile)
            print('-files converted to df')
            self.transform_df_orass()
            print(self.df.head(5))
            self.transform_dates()
            print('-df in a right format')
        except:
            self.df = pd.DataFrame()
            print(xfile + ' do not exist -> df is empty')

        
        print('-SQL DB to be created ...')
        self.setup_sql()
        #traiter la table orass(table brute)
        print('-new table process begin ...')
        self.export_to_sql_initTables_new(name_table)
        print('-... new table table END')
      
        
        print()
        print('-Process all done')

        t_end = time.perf_counter()
        deltaT= t_end - t_start
        minutes, secondes = divmod(deltaT, 60)
        print('-Table created on {:02d}mn{:02d}sec'.format(int(minutes),int(secondes)))


    
if __name__ == '__main__':
    '''
    prerequisite: define the name of database ex : db='dbCAR'
    runing on docker : host = database_mngt (docker) ; on pc: host = localhost
    ex: app.py filename username password host
    python app.py file.xlsx postgres aro database_mngt
    '''
    
    db = dbNH()

    #postgres cred
    db.sql['db'] = os.environ.get('DATABASE')
    db.sql['user'] = os.environ.get('USER')
    db.sql['pw'] = os.environ.get('PASSWORD')
    db.sql['host'] = os.environ.get('HOST')
    db.sql['port'] = os.environ.get('PORT')

   

    
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='context' , choices=['test', 'nh'],help='context help')
    parser.add_argument('-f', '--file',dest='file' , type=str, help='file help')
    parser.add_argument('-d','--date',dest='dateExtract',type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'),)
    parser.add_argument('-t','--table',dest='tableName',type=str)


    args = parser.parse_args()
    
    if (args.context == 'nh') & (args.dateExtract == None):
        print("Besoin d'un argument DATE")
        exit()

    if (args.context == 'nh') & (args.tableName == None):
        print("Besoin d'un argument TableName")
        exit()

    else:
        db.dt_orassExtraction  = args.dateExtract

    
    #print(args.dateExtract)
    #exit()



    ##import file orass
    if args.context == 'nh':
        db.run_importXlsFile_nh(args.file, args.tableName)

    elif args.context == 'test':
        db.query = "SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';" 
        db.run_query_printRes()
        print(db.queryRes)

        #print(rqt_orass)
        #print(rqt_sage)




        
    


    ##Run a query
    #db.query = "SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';" 
    #db.query = "SELECT COUNT(*) FROM etat_quittance;"
    #db.query = "SELECT COUNT(*) FROM recouvrement;"

    #db.query = "SELECT DISTINCT date_extraction FROM etat_quittance ORDER BY date_extraction;db.query = "SELECT * FROM recouvrement;"
    #db.run_query_printRes()
    #print(db.queryRes)


    ##View datatype
    #db.query = """ SELECT column_name,
    #                CASE
    #                    WHEN domain_name is not null then domain_name
    #                    WHEN data_type='character varying' THEN 'varchar('||character_maximum_length||')'
    #                    WHEN data_type='numeric' THEN 'numeric('||numeric_precision||','||numeric_scale||')'
    #                    ELSE data_type
    #                END AS myType
    #                FROM information_schema.columns
    #                WHERE table_name='recouvrement'
    #                ;
                    
                    
    #"""
    #db.run_query_printRes()
    #print(db.queryRes)

    
    ## DROP & Create Table
    #table = "recouvrement"
    #db.query = f'DROP TABLE IF EXISTS {table};'
    #db.query += f'''CREATE TABLE {table} 
    #        (
    #            id SERIAL,
    #            date_saisie TEXT,
    #            souscripteur_nom VARCHAR(50),
    #            prime_montant BIGINT,
    #            garantie_type VARCHAR(10),
    #            garantie_montant BIGINT,
    #            account_montant BIGINT,
    #            account_reference VARCHAR(20),
    #            commentaire VARCHAR(255),
    #            recouvrement_situation VARCHAR(20) 
    #        );     
    #        '''
    #db.run_query()

    ## Insert for recouvrement table
    #db.query = """
    #            INSERT INTO recouvrement (code_souscripteur, num_police, date_action, commentaire)
    #                VALUES(300,300000, '2021/6/4', 'client reglo 2') 
    #                RETURNING id;
    # 
    #          """
    #db.run_query()
    

