# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
import pandas as pd
import random
import spacy
import difflib
from pandas import Series
from num2words import num2words
from rasa_sdk.events import AllSlotsReset
import openai
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

#caricamento della chiave di SERPAPI
load_dotenv()
SERPAPI_API_KEY = os.getenv('SERPAPI_KEY')

dict_portate ={ "a":"antipasto","p":"primo","s":"secondo","c":"contorno","d": "dessert","ca":"Carne","po":"Pollame","pe":"Pesce"}

# Load the spaCy model for the Italian language
nlp = spacy.load("it_core_news_sm")

pd.set_option('display.max_colwidth', None)


def word_in_string(word_list, string):
    count = 0
    for word in word_list:
        word_lower = word.lower()
        string_lower = string.lower()
        if word_lower in string_lower:
            count += 1
    return count


def generate_image(nome_ricetta,tipo):
    if tipo=="Bevande": tipo="cocktail"
    params = {
        "q": "ricetta " + tipo + " " + str(nome_ricetta),
        "tbm": "isch",
        "ijn": 0,
        "api_key": SERPAPI_API_KEY.strip()
    }    
    search = GoogleSearch(params)
    try:
        link = search.get_dict()['images_results'][0]["original"]
    except:
        return ""
    
    return link

def filter_by_ingredients(list_ingredienti_word,filter):    
    colonne = {'id_ricetta': [], 'nome': [], 'tipo': [], 'ing_principale': [], 'n_persone': [], 'note': [], 'preparazione': [], 'quantita': [], 'nome_ingrediente': [], 'calorie': []}
    filter2 = pd.DataFrame(colonne)   

    #num_ingredienti = 0
    for j in range(0, len(list_ingredienti_word)):
        value = False
        for i, row in filter.iterrows():
            if (word_in_string(list_ingredienti_word, row['nome_ingrediente']) == len(list_ingredienti_word) - j):
                filter2 = filter2.append(row, ignore_index=True)
                #num_ingredienti = len(lista) - j
                value = True
                continue
            if len(filter2) == 2:
                    break

            if value: break
        if len(filter2) == 2:
                break
    return filter2

def correct_words(list_ingredienti_word):
    # CORREZIONE DELLE STRINGHE
    lista_parole_corrette = []
    for ingredienti_singoli_word in list_ingredienti_word:                       
        correct_word = difflib.get_close_matches(ingredienti_singoli_word, single_word_list, n=1, cutoff=0.6)
        if correct_word:
            lista_parole_corrette.append(correct_word[0])
    return lista_parole_corrette
    


def to_dict(x):
     return Series(dict( quantita = "{%s}" % ', '.join(x['quantita']),
                        nome_ingrediente = "{%s}" % ', '.join(x['nome_ingrediente']),
                        calorie = x['calorie'].sum()))

def find_rows(strings, df, name_column):
    if len(strings) != 0:
        result = df[df[name_column].str.lower() == "".join(strings).lower()]
        if len(result)>0:
            return result
        result = df
        for string in strings:
            result = result[result[name_column].str.lower().str.contains(string.lower(),regex=False)]
    else:
        result = []
    return result


def buildResponse(df,dispatcher):
        output = ""
        for index, row in df.iterrows():
            t = "persone"
            if row['n_persone'] == 1: t = "persona"
            immagine_url =generate_image(row['nome'],str(row["tipo"]))
            if immagine_url != "":
                dispatcher.utter_message(image=immagine_url)
            output += "  \n \n"
            output += f"<b>{str(row['nome']).upper()}</b> \n \n"
            output += f"<b>Tipo di piatto:</b> {row['tipo']} \n"
            output += f"<b>Ingrediente principale:</b> {str(row['ing_principale'])} \n"
            output += f"Dosaggio per <b>{str(int(row['n_persone']))} {t} </b>\n"
            output += f"<b>Ingredienti:</b>\n"
            nome_ingredienti = str(row["nome_ingrediente"]).replace("{","").replace("}","").split(",")
            quantita = str(row["quantita"]).replace("{","").replace("}","").split(",")

            for n,q in zip(nome_ingredienti,quantita):
                output += q.strip() + " - " + n.strip() + "\n"
            output += f"<b>Calorie totali:</b> " + str(row["calorie"]) + " cal \n"
            output += f"<b>Procedimento:</b> {str(row['preparazione'])} \n"
            output += f"<b>Note aggiuntive:</b> {str(row['note'])} \n"
            dispatcher.utter_message(json_message={"text":output,"parse_mode":"HTML"})
            output = ""

def all_lower(my_list):
    return [x.lower() for x in my_list]


df_ingredients = pd.read_csv('./actions/dataset_ricette/ingredienti.csv')
df_recipe = pd.read_csv('./actions/dataset_ricette/ricette.csv')

ingredienti_possibili = df_recipe["ing_principale"].tolist()

ingredienti_possibili = list(set(ingredienti_possibili))
ingredienti_possibili = all_lower(ingredienti_possibili)

# CREAZIONE DELLA LISTA DELLE SINGOLE PAROLE PER LA EVENTUALE CORREZIONE DELLE STESSE
single_word_list = []
for phrase in ingredienti_possibili:
    words = phrase.split()
    for word in words:
        single_word_list.append(word)
single_word_list = list(set(single_word_list))


# POSSIBILI NUMERI DI PERSONE
num_persone_possibili_parole = []
num_persone_possibili_int = df_recipe["n_persone"].tolist()
num_persone_possibili = [str(numero) for numero in num_persone_possibili_int]
num_persone_possibili = list(set(num_persone_possibili))
num_translator = {}
for num_persone in num_persone_possibili:
    num_persone_possibili_parole.append(num2words(int(num_persone),lang="it"))
    num_translator[num2words(int(num_persone),lang="it")] = num_persone
num_persone_possibili = num_persone_possibili + num_persone_possibili_parole



# POSSIBILI PORTATE
portate_possibili = df_recipe["tipo"].tolist()
portate_possibili = list(set(portate_possibili))
portate_possibili = all_lower(portate_possibili)



# PAROLE DA ESCLUDERE NELLA RICERCA DELL'INGREDIENTE
list_parole_da_escludere = df_recipe["tipo"].tolist()
list_parole_da_escludere = list(set(list_parole_da_escludere))
list_parole_da_escludere = all_lower(list_parole_da_escludere)
list_parole_da_escludere.append('ricetta')
list_parole_da_escludere.append('ingrediente')
list_parole_da_escludere.append('ingredienti')
list_parole_da_escludere.append('persone')
list_parole_da_escludere.append('nome')

list_parole_da_escludere_con_carne = df_recipe["tipo"].tolist()
list_parole_da_escludere_con_carne = list(set(list_parole_da_escludere))
list_parole_da_escludere_con_carne = all_lower(list_parole_da_escludere)
list_parole_da_escludere_con_carne.append('ricetta')
list_parole_da_escludere_con_carne.append('ingrediente')
list_parole_da_escludere_con_carne.append('ingredienti')
list_parole_da_escludere_con_carne.append('persone')
list_parole_da_escludere_con_carne.append('nome')
list_parole_da_escludere_con_carne.append('carne')

buttons = [{
            "title": "Carne", 
            "payload": '/scelta_secondo{"secondo":"ca"}'
            },
           {
           "title": "Pollame", 
           "payload": '/scelta_secondo{"secondo":"po"}'
           },
           {
           "title": "Pesce", 
           "payload": '/scelta_secondo{"secondo":"pe"}'
           }
          ]




class MyFallback(Action):
    
    def name(self) -> Text:
        return "action_my_fallback"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        dispatcher.utter_message(response = "utter_fallback")
        return []



class ResetSlot(Action):

    def name(self):
        return "action_azzera_slot"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Operazione annullata.")
        return [AllSlotsReset()]



class ValidateRicettaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_ricetta_form"
    
    
    

    def validate_ingredienti_ricetta(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict):
        """Validate `ingredienti_ricetta` value."""
        

        slot_ingredienti = ""
        slot_portata = ""
        slot_num_persone = ""

        # ANALISI NLP SINTASSI
        doc = nlp(tracker.latest_message["text"])

        # LISTA VUOTA PER LE PAROLE TROVATE DALLA SINTASSI
        list_ingredienti_word = []

        # RICERCA DELLE PAROLE CHIAVE (NOMI, AGGETTIVI ECC.) PER LA RICERCA DELL'INGREDIENTE, DELLA PORTATA E DEL NUMERO DI PERSONE
        if tracker.get_slot("ingredienti_ricetta") == None:
            lista_esclusioni = list_parole_da_escludere
        else:
            lista_esclusioni = list_parole_da_escludere_con_carne
        for token in doc:
            if token.text.lower() in lista_esclusioni:
                if token.text.lower() in portate_possibili:
                    slot_portata = token.text.lower()
                continue
            if token.pos_ == 'NUM':
                slot_num_persone = token.text.lower()
            if token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'ADV' or token.pos_ == 'ADJ':
                list_ingredienti_word.append(token.text.lower())

        list_ingredienti_word = list(set(map(str.lower, slot_value + list_ingredienti_word)))
        
        if len(list_ingredienti_word) > 1: # se l'utente ha inserito pi?? di un ingrediente
            # ricerca tra tutti gli ingredienti

            if slot_portata: filter = df_recipe[df_recipe['tipo'].str.lower().str.contains(slot_portata.lower())]
            else: filter = df_recipe

            

            result = filter_by_ingredients(list_ingredienti_word,filter)

            if len(result) > 0: # se ?? stata trovata una ricetta con quegli ingredienti
                lista_ing = set(list_ingredienti_word)
                lista_ingredienti = list(lista_ing)
            else:
                # si prova a correggere le parole e si ripete la ricerca
                lista_parole_corrette = correct_words(list_ingredienti_word)
                result = filter_by_ingredients(lista_parole_corrette, filter)
                lista_ingredienti = list(set(result["ing_principale"].to_list()))
            if len(lista_ingredienti) >0: slot_ingredienti = lista_ingredienti
            else:
                dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con gli ingredienti scelti.")
                return {"ingredienti_ricetta": None}
        else:   # se l'utente ha inserito un solo ingrediente, si ricerca su ingrediente principale
            # RICERCA DELL'INGREDIENTE
            result = find_rows(list_ingredienti_word, df_recipe,"ing_principale")
            if len(result) > 0:    
                lista_ing = set(result["ing_principale"].to_list())
                lista_ingredienti = list(lista_ing)
                if len(lista_ingredienti) >0 : slot_ingredienti = [random.choice(lista_ingredienti)]
                else:
                    lista_parole_corrette = correct_words(list_ingredienti_word)
                    result = self.find_rows(lista_parole_corrette, df_recipe,"ing_principale")
                    lista_ingredienti = list(set(result["ing_principale"].to_list()))
                    if len(lista_ingredienti) >0: slot_ingredienti = [random.choice(lista_ingredienti)]
                    else:
                        dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con questo ingrediente.")
                        return {"ingredienti_ricetta": None}
            else:
                slot_ingredienti = None
                # dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con questo ingrediente.")
                # return {"ingredienti_ricetta": None}
        ingr_str = ", ".join(slot_ingredienti)
        # SE L'UTENTE DA L'INGREDIENTE E LA PORTATA
        if not slot_portata == "" and slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta con {ingr_str} per un {slot_portata}.")
            return {"ingredienti_ricetta": slot_ingredienti, "portata_ricetta": slot_portata, "nome_ricetta": None}
        # SE L'UTENTE DA L'INGREDIENTE LA PORTATA E IL NUMERO DI PERSONE
        elif not slot_portata == "" and not slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta con {ingr_str}, per un {slot_portata}, per {slot_num_persone} persone. \n\nRicerca ricetta in corso...")
            return {"ingredienti_ricetta": slot_ingredienti, "portata_ricetta": slot_portata, "num_persone_ricetta": slot_num_persone, "nome_ricetta": None}
        # SE L'UTENTE DA L'INGREDIENTE E IL NUMERO DI PERSONE
        elif slot_portata == "" and not slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta con {ingr_str}, per {slot_num_persone} persone.")
            return {"ingredienti_ricetta": slot_ingredienti, "num_persone_ricetta": slot_num_persone, "nome_ricetta": None}
         # SE L'UTENTE DA L'INGREDIENTE E IL NUMERO DI PERSONE
        elif not slot_portata == "" and slot_ingredienti == []:
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta per un {slot_portata}.")
            return {"ingredienti_ricetta": slot_ingredienti, "num_persone_ricetta": slot_num_persone, "nome_ricetta": None}
        # SE L'UTENTE DA L'INGREDIENTE
        if not slot_ingredienti == None:
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta con {ingr_str}.")
            return {"ingredienti_ricetta": slot_ingredienti, "nome_ricetta": None}

        dispatcher.utter_message(text=f"Inserisca almeno un termine di ricerca, grazie!")
        return {"ingredienti_ricetta": slot_ingredienti, "nome_ricetta": None}

    def validate_portata_ricetta(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `portata_ricetta` value."""
        if slot_value not in portate_possibili:
            correct_word = difflib.get_close_matches(slot_value,portate_possibili, n=1, cutoff=0.6)
            if not correct_word:       
                dispatcher.utter_message(text=f"Mi dispiace ma non abbiamo questo tipo di portata tra le nostre ricette. Possiamo accettare: {'/'.join(portate_possibili)}.")
                return {"portata_ricetta": None, "nome_ricetta": None}
            else: 
                slot_value = correct_word[0]
        
        slot_portata = slot_value
        slot_num_persone = tracker.get_slot("num_persone_ricetta")
        slot_ingredienti = tracker.get_slot("ingredienti_ricetta")
        #print("ingredienti:",slot_ingredienti)
        if slot_ingredienti != [] and slot_ingredienti != None : ingr_str = ", ".join(slot_ingredienti)
        #dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta da {slot_value}.")
        if tracker.get_slot("ingredienti_ricetta") != None and tracker.get_slot("portata_ricetta") != None and tracker.get_slot("num_persone_ricetta") != None:
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta con {ingr_str}, per un {slot_portata}, per {slot_num_persone} persone. \n\nRicerca ricetta in corso...")
        else:
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta da {slot_portata}.")
        return {"portata_ricetta": slot_value, "nome_ricetta": None}

    def validate_num_persone_ricetta(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `num_persone_ricetta` value."""
        if slot_value not in num_persone_possibili:
           
            correct_word = difflib.get_close_matches(slot_value,num_persone_possibili, n=1, cutoff=0.6)
            if not correct_word:       
                dispatcher.utter_message(text=f"Mi dispiace ma non abbiamo questo numero di persone. Possiamo accettare: {'/'.join(num_persone_possibili)}.")
                return {"num_persone_ricetta": None, "nome_ricetta": None}
            else: 
                slot_value = correct_word[0]
        
        try:
            int(slot_value)
        except:
            slot_value = num_translator[slot_value]
        
        slot_num_persone = slot_value
        slot_portata = tracker.get_slot("portata_ricetta")
        slot_ingredienti = tracker.get_slot("ingredienti_ricetta")
        if slot_ingredienti != [] and slot_ingredienti != None : ingr_str = ", ".join(slot_ingredienti)
        if tracker.get_slot("ingredienti_ricetta") != None and tracker.get_slot("portata_ricetta") != None and tracker.get_slot("num_persone_ricetta") != None:
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta con {ingr_str}, per un {slot_portata}, per {slot_num_persone} persone. \n\nRicerca ricetta in corso...")
        else:
            dispatcher.utter_message(text=f"Va bene! Cercher?? una ricetta per {slot_num_persone} persone.")
        return {"num_persone_ricetta": slot_num_persone, "nome_ricetta": None}





class ValidateNomeRicettaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_nome_ricetta_form"
    
    def validate_nome_ricetta(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict):
        """Validate `nome_ricetta` value."""

        #print(slot_value)
        # ANALISI NLP SINTASSI
        nome_ricetta_slot = ""
        doc = nlp(tracker.latest_message["text"])
        
        # LISTA VUOTA PER LE PAROLE TROVATE DALLA SINTASSI
        list_ricetta_word = []
        lista_esclusioni = list_parole_da_escludere
        # RICERCA DELLE PAROLE CHIAVE (NOMI, AGGETTIVI ECC.) PER LA RICERCA DELL'INGREDIENTE, DELLA PORTATA E DEL NUMERO DI PERSONE
        for token in doc:
            if token.text.lower() in lista_esclusioni:
                continue
            if token.pos_ in ['NOUN','PROPN','ADV']:
                list_ricetta_word.append(token.text.lower())
        if len(list_ricetta_word) == 0:
            list_ricetta_word.append(tracker.get_slot("nome_ricetta"))
        # PRINTI DELLA SINTASSI DELLE STRINGHE
        #print("Lista delle stringhe che ci aiutano a trovare la ricetta: " + str(list_ricetta_word))
        syntax_divisions = [(token.text, token.pos_) for token in doc]
        #print("La divisione della sintassi: " + str(syntax_divisions))

        # RICERCA DELL'INGREDIENTE
        result = find_rows(list_ricetta_word, df_recipe,"nome")
        
        if len(result) > 0:
            lista_ricette = list(set(result["nome"].to_list()))
            nome_ricetta_slot = random.choice(lista_ricette)
        else:
            dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta :'(")
            return {"nome_ricetta": None, "ingredienti_ricetta": None, "portata_ricetta": None, "num_persone_ricetta": None}
        dispatcher.utter_message(text=f"Va bene! Cercher?? la ricetta {nome_ricetta_slot}. \n\nRicerca ricetta in corso...")
        return {"nome_ricetta": nome_ricetta_slot, "ingredienti_ricetta": None, "portata_ricetta": None, "num_persone_ricetta": None}




class ActionCreazioneRicette(Action):
    def name(self) -> Text:
        return "action_ricetta"
    
    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("nome_ricetta") != None:
            #print("Il nome da cercare ??: " + str(tracker.get_slot("nome_ricetta")))
            
            nome = tracker.get_slot("nome_ricetta")
            ricette = df_recipe[df_recipe['nome'].str.lower().str.contains(nome.lower(),regex=False)]
            
            if len(ricette)==0 : 
                output = "Non ci sono ricette con questo nome."
            else:
                if len(ricette) >= 2: 
                    ricette = ricette.sample(n=2)
                buildResponse(ricette,dispatcher)

            return [AllSlotsReset()]

        elif tracker.get_slot("ingredienti_ricetta") != None or tracker.get_slot("portata_ricetta") != None or tracker.get_slot("num_persone_ricetta") != None:
            #print("La ricetta da cercare ?? con ingredienti, portata o numero di persone")
            ingredienti_slot = tracker.get_slot("ingredienti_ricetta")
            ricette = pd.DataFrame()
            output = ""
            if ingredienti_slot != None:
                ingredienti_slot_l = ingredienti_slot
                if len(ingredienti_slot_l) == 1:
                    # ricerca di Meeett
                    ricette = df_recipe[df_recipe['ing_principale'].str.lower().str.contains(ingredienti_slot[0].lower(),regex=False)].reset_index()

                else:
                    # ricerca di Simone
                    slot_portata = tracker.get_slot("portata_ricetta")
                    if slot_portata: filter = df_recipe[df_recipe['tipo'].str.lower().str.contains(slot_portata.lower())]
                    else: filter = df_recipe
                    ricette = filter_by_ingredients(ingredienti_slot_l, filter)
                
            portata_slot = tracker.get_slot("portata_ricetta")
            num_persone_slot = tracker.get_slot("num_persone_ricetta")
            try:
                int(num_persone_slot)
            except:
                num_persone_slot = num_translator[num_persone_slot]
            
            
            if tracker.get_slot("portata_ricetta") != None:
                ricette = ricette[ricette['tipo'].str.lower().str.contains(portata_slot.lower(),regex=False)].reset_index()
            if tracker.get_slot("num_persone_ricetta") != None:
                ricette_n_persone = ricette
                
                if len(ricette_n_persone.loc[ricette_n_persone['n_persone'] == str(num_persone_slot)]) < 2:
                    ricette_n_persone = ricette_n_persone.sample(2)
                else:
                    ricette_n_persone = ricette_n_persone.loc[ricette_n_persone['n_persone'] == str(num_persone_slot)].head(2)

                if len(ricette) == 0:
                    output = "Non ci sono ricette con queste caratteristiche."
                    dispatcher.utter_message(text=output)
                    return [AllSlotsReset()]
                if int(num_persone_slot) not in ricette_n_persone["n_persone"].to_list():
                    output += "Non ?? stata trovata una ricetta con il numero di persone scelto. \n"
                    output += "Prover?? comunque a cercare una ricetta ;). \n"
                    dispatcher.utter_message(text=output)
                    output = ""
                
                

                ricette = ricette_n_persone

            if len(ricette)==0 : 
                output = "Non ci sono ricette con queste caratteristiche."
                dispatcher.utter_message(text=output)
                return [AllSlotsReset()]
            else:
                if len(ricette) >= 2: 
                    ricette = ricette.sample(n=2)
                buildResponse(ricette,dispatcher)

            return [AllSlotsReset()]
                
        return [AllSlotsReset()]


class ActionCreazioneMenu(Action):
    def name(self) -> Text:
        return "action_crea_menu"
    
    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot("portate") != None:
            portate = list(tracker.get_slot("portate"))
            if "s" in portate:
                portate.remove("s")
                dispatcher.utter_message(text="Quale secondo vuoi?", buttons = buttons)
                return [SlotSet("portate", portate)]
            else:
                ricette = []
                if tracker.get_slot("secondo") != None:
                    if "a" in portate:
                        portate.insert(2, tracker.get_slot("secondo"))
                    else:
                        portate.insert(1, tracker.get_slot("secondo"))
                for portata in portate:
                    ricette.append(df_recipe[df_recipe["tipo"].str.lower() == str(dict_portate[portata]).lower()].sample(n=1))
                for ricetta in ricette:                    
                    buildResponse(ricetta,dispatcher)
                    

            return [AllSlotsReset()]
        
        return [AllSlotsReset()]

class ActionRicettaRandom(Action):
    def name(self) -> Text:
        return "action_ricetta_random"
    
    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Va bene, ti fornir?? una ricetta casuale.")
        
        buildResponse(df_recipe.sample(n=1),dispatcher)
        
        return [AllSlotsReset()]