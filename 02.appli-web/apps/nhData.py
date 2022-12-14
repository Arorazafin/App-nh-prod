# standard package
from datetime import datetime
import pandas as pd
import numpy as np

## function
def func_checking(agences):    
    data_checking = [
        [k,
        v[1],
        len(["containsNan" for x in v[2]['Code souscripteur'] if pd.isna(x)]),
        len(["contains:" for y in v[2]['Prime totale quittance'] if ":" in str(y) ]),
        ] for k,v in agences.items() if not v[2].empty
    ]
    
    checking = dict()
    df_checking = pd.DataFrame(data = data_checking , columns = ['code','agence','ErreurCS','ErreurPTQ'])
    checking = {
        'df':df_checking,
        'ErreurCS': df_checking['ErreurCS'].sum(),
        'ErreurPTQ': df_checking['ErreurPTQ'].sum(),
        'erreur' : df_checking['ErreurCS'].sum()+df_checking['ErreurCS'].sum()
    }
    
    
    return checking

def NumQuittanceSelectionForNan(df):
    lsNumQ = [row['Num quittance'] for index, row in df.iterrows() if pd.isna(row['Code souscripteur'])]
    return lsNumQ

def NumQuittanceselectionForDate(df):
    lsNumQ = [row['Num quittance'] for index, row in df.iterrows() if ":" in str(row['Prime totale quittance'])]
    return lsNumQ

def decalage (df,numQ, col):
    y = df[df['Num quittance'] == numQ]
    idx = y.index[0]
    colRef = y.columns.tolist().index(col)
    while colRef < len(y.columns)-1:
        df.loc[idx,y.columns[colRef]] = y[y.columns[colRef+1]].tolist()[0]
        colRef = colRef+1
    return df

def decalageMain(df,erreur):
    if erreur == "ErreurCS":
        ls = NumQuittanceSelectionForNan(df)
        for  l in ls:
            df = decalage (df,l, 'Code souscripteur')
    elif erreur == "ErreurPTQ":
        ls = NumQuittanceselectionForDate(df)
        for  l in ls:
            df = decalage (df,l, 'Adresse Ass')
    return df

def func_reguler(df_checking, agences):
    for i, r in df_checking.iterrows():
       # if not nh_agences[r['code']][2].empty():
            if r['ErreurCS']>0:
                agences[r['code']][2]= decalageMain(agences[r['code']][2],'ErreurCS')
            if r['ErreurPTQ']>0:
                agences[r['code']][2]= decalageMain(agences[r['code']][2],'ErreurPTQ')
    return agences

def change_type(agences):
#cols chmt de type "Prime totale quittance"  -> float
    for k,v in agences.items():
        print(k)
        v[2] = v[2].astype({"Prime totale quittance": float })
        v[2]["Prime totale quittance"] = v[2]["Prime totale quittance"].fillna(0)
        print("Prime totale quittance OK")
        v[2] = v[2].astype({"Code souscripteur": int })
        print("Code souscripteur OK")
        #rempalcer les na par 0
        try:
            v[2] = v[2].astype({"Montant Encaiss?? quittance": float})
        except:
            err = v[2][v[2]["Montant Encaiss?? quittance"]==np.datetime64("NaT")]
            print(err) 
            v[2]["Montant Encaiss?? quittance"] =  v[2]["Montant Encaiss?? quittance"].fillna(np.nan).replace([np.nan], [0])
        v[2] = v[2].astype({"Montant Encaiss?? quittance": float})
        v[2]["Montant Encaiss?? quittance"] = v[2]["Montant Encaiss?? quittance"].fillna(0)
        print("Montant Encaiss?? quittance OK")
    return agences