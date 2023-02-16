import pandas as pd
import json 
import os
# SETTING DELLE CARTELLE DI INPUT E DI OUTPUT CONTENENTI I FILE

INPUT_DIR = "./dataset-generation/dbrice13_original/"
OUTPUT_DIR = "./dataset-generation/dataset_output/"

###############################################################


# funzione che restituisce una lista del tipo [quantita, calorie]
def ing_q_cal(l):
    
    l = l.split(" ==== ")
    if len(l) == 1:
        el = l[0].split("==== ")
        l = []
        if len(el) > 1:
            l.append(el[0])
            l.append(el[1])
        else:
            l.append("")
            l.append(el[0])
    return l

def getter(x):
    return pd.Series(dict( quantita = "{%s}" % ', '.join(x['quantita']), 
                        nome_ingrediente = "{%s}" % ', '.join(x['nome_ingrediente']),
                        calorie = x['calorie'].sum()))

# INIZIALIZZAZIONI VARIABILI
tot_len = 0
id_ricetta = 0
id_ingredienti = 0
dict_ricetta = {}
row = []
data = []
lista_ingredienti = []
c = ""
l1 = ""

# Lettura file di testo contenente le ricette e parsing
with open(INPUT_DIR+'ricette.txt') as f:
    lines = f.readlines()
    for l in lines:
        l = l.strip()
        if l == ":Ricette": 
            if c == "prep":
                data.append(l1.strip())
                
                row.append(data)
                data = []
                l1 = ""
            id_ricetta += 1
            data.append(id_ricetta)
            continue
        elif l == "-Nome": 
            c="n"
            continue
        elif c == "n": 
            data.append(l)
            c = "t"
            continue
        elif l == "-Tipo_Piatto":
            continue
        elif c=="t":
            data.append(l)
            c = "i"
            continue
        elif l == "-Ing_Principale":
            continue
        elif c == "i":
            data.append(l)
            c = "p"
            continue
        elif l == "-Persone":
            continue
        elif c == "p":
            data.append(l)
            c = "no"
            continue
        elif l == "-Note":
            continue
        elif c == "no":
            data.append(l)
            c = "ing"
            continue
        elif l == "-Ingredienti":
            continue
        elif c == "ing":
            c = "l_ing"
            id_ingredienti += 1
            # data.append(id_ingredienti)
            if ':' in l: continue
            l = ing_q_cal(l)
            lista_ingredienti.append(l)
            
            continue
        elif c == "l_ing":
            if l == "-Preparazione":
                dict_ricetta[str(id_ingredienti)] = lista_ingredienti
                lista_ingredienti = []
                c = "prep"
                continue
            else:
                if ':' in l: continue
                l = ing_q_cal(l)
                lista_ingredienti.append(l)
                continue
        elif c == "prep":
            l1 = l + " "
            continue

# generazione dataframe ricette
df_ricette = pd.DataFrame(row, columns=['id_ricetta','nome','tipo','ing_principale','n_persone','note','preparazione'])

df_ricette =df_ricette.mask(df_ricette == '')
df_ricette["ing_principale"] = df_ricette["ing_principale"].fillna("non specificato")

# Gli ingredienti delle ricette sono salvati su un dizionario che contiene :
# key -> id_ricetta ; value -> lista di coppie [nome_ingrediente, quantità]
with open(OUTPUT_DIR+"ingredienti.json","w",encoding="utf-8") as outfile:
    json.dump(dict_ricetta,outfile)


data_ing_cal = []
# Lettura file di testo contenenti gli ingredienti totali con le calorie legate alle quantità
with open(INPUT_DIR+'ing.txt') as f:
    lines = f.readlines()
    lines.pop(0)
    for l in lines:
        l = l.strip()
        l = l.replace("_ING","")
        l1 = l.split(" == ")
        nome = l1[0]
        l2 = l1[1].split(" === ")
        quantita = l2[0]
        calorie = l2[1]
        data_ing_cal.append([nome,quantita,calorie])

data = []

# utilizziamo il dizionario per creare un dataframe che poi verrà utilizzato per legare
# l'ingrediente alla ricetta e alle sue calorie, attraverso un merge tra i 2 dataframe utilizzando
# come chiavi il nome dell'ingrediente e la quantità 
for key in dict_ricetta:
    for ingredient in dict_ricetta[key]:
        data.append([key, ingredient[0], ingredient[1]])
df_ingredienti = pd.DataFrame(data, columns=["id_ricetta", "quantita", "nome_ingrediente"])
df_ingredienti['quantita'] = df_ingredienti['quantita'].replace("","0")

# creazione del dataset ingredienti attraverso un merge. Il dataset contiene le seguenti colonne:
# - id della ricetta in cui viene utilizzato l'ingrediente
# - quantita utilizzata nella ricetta
# - nome dell'ingrediente
# - calorie dell'ingrediente
df_ingredienti_cal = pd.DataFrame(data_ing_cal, columns=["nome_ingrediente", "quantita", "calorie"])
df_ingredienti_cal = df_ingredienti.merge(df_ingredienti_cal,on=["nome_ingrediente","quantita"],how='left')
df_ingredienti_cal['quantita'] = df_ingredienti_cal['quantita'].replace("0","q.b.")
df_ingredienti_cal['calorie'] = df_ingredienti_cal['calorie'].fillna(16)
df_ingredienti_cal = df_ingredienti_cal.drop_duplicates()

df_ingredienti_cal.to_csv(OUTPUT_DIR+"ingredienti.csv",index=False)

df_ingredienti_cal = pd.read_csv(OUTPUT_DIR+"ingredienti.csv")
df_union = df_ingredienti_cal.groupby('id_ricetta').apply(getter).reset_index()

df_ricette = pd.merge(left = df_ricette, right = df_union, on = 'id_ricetta', how = 'right')
df_ricette = df_ricette.dropna(axis='index', how='any')

# salvataggio del dataset nella cartella specificata in OUTPUT_DIR
df_ricette.to_csv(OUTPUT_DIR + "ricette.csv",index=False)
df_ingredienti_cal.to_csv(OUTPUT_DIR+"ingredienti.csv",index=False)

print("## CREAZIONE DATASET AVVENUTA CON SUCCESSO NELLA CARTELLA:", OUTPUT_DIR, "##")
print("credit DB: www.dbricette.it")