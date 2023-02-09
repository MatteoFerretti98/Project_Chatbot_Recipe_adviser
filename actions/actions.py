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
                    
            if value: break
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

'''
def get_ingredienti(id_ricetta):
        df = df_ingredients[df_ingredients["id_ricetta"] == id_ricetta]
        df = df.drop(columns=["id_ricetta"])
        out = df.to_string(index=False) + "\n \n"
        out += f"Calorie complessive: {str(sum(df['calorie']))} \n \n"
        return out
'''

def buildResponse(df):
        output = ""
        for index, row in df.iterrows():
            output += "  \n \n"
            output += f"Nome: {row['nome']} \n"
            output += f"Tipo di piatto: {row['tipo']} \n"
            output += f"Ingrediente principale: {str(row['ing_principale'])} \n"
            output += f"Numero di persone: {str(row['n_persone'])} \n"
            output += f"Note: {str(row['note'])} \n"
            output += f"Ingredienti: " + row["nome_ingrediente"] + "\n"
            output += f"Preparazione: {str(row['preparazione'])}"
        
        return output

def all_lower(my_list):
    return [x.lower() for x in my_list]


df_ingredients = pd.read_csv('./actions/dataset_ricette/ingredienti.csv')
df_recipe = pd.read_csv('./actions/dataset_ricette/ricette.csv')


df2 = df_ingredients.groupby('id_ricetta').apply(to_dict).reset_index()
df_recipe = pd.merge(left = df_recipe, right = df2, on = 'id_ricetta', how = 'right')
df_recipe = df_recipe.dropna(axis='index', how='any')


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

buttons = [{
            "title": "Carne", 
            "payload": '/scelta_secondo{"secondo":"Carne"}'
            },
           {
           "title": "Pollame", 
           "payload": '/scelta_secondo{"secondo":"Pollame"}'
           },
           {
           "title": "Pesce", 
           "payload": '/scelta_secondo{"secondo":"Pesce"}'
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
        print(tracker.slots)
        print(slot_value)

        print(tracker.latest_message["text"])
        # LISTA VUOTA PER LE PAROLE TROVATE DALLA SINTASSI
        list_ingredienti_word = []

        # RICERCA DELLE PAROLE CHIAVE (NOMI, AGGETTIVI ECC.) PER LA RICERCA DELL'INGREDIENTE, DELLA PORTATA E DEL NUMERO DI PERSONE
        for token in doc:
            if token.text.lower() in list_parole_da_escludere:
                if token.text.lower() in portate_possibili:
                    slot_portata = token.text.lower()
                continue
            if token.pos_ == 'NUM':
                slot_num_persone = token.text.lower()
            if token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'ADV' or token.pos_ == 'ADJ':
                list_ingredienti_word.append(token.text.lower())

        #portata = str(tracker.get_slot('portata_ricetta'))
        print(slot_portata)
        print(list_ingredienti_word)

        # PRINTI DELLA SINTASSI DELLE STRINGHE
        print("Lista delle stringhe che ci aiutano a trovare l'ingrediente: " + str(list_ingredienti_word))
        syntax_divisions = [(token.text, token.pos_) for token in doc]
        print("La divisione della sintassi: " + str(syntax_divisions))
        
        if len(list_ingredienti_word) > 1: # se l'utente ha inserito più di un ingrediente
            # ricerca tra tutti gli ingredienti

            if slot_portata: filter = df_recipe[df_recipe['tipo'].str.lower().str.contains(slot_portata.lower())]
            else: filter = df_recipe

            

            result = filter_by_ingredients(list_ingredienti_word,filter)

            if len(result) > 0: # se è stata trovata una ricetta con quegli ingredienti
                lista_ing = set(list_ingredienti_word)
                lista_ingredienti = list(lista_ing)
            else:
                # si prova a correggere le parole e si ripete la ricerca
                lista_parole_corrette = correct_words(list_ingredienti_word)
                print(lista_parole_corrette)
                result = filter_by_ingredients(lista_parole_corrette, filter)
                print(result)
                lista_ingredienti = list(set(result["ing_principale"].to_list()))
            if len(lista_ingredienti) >0: slot_ingredienti = ", ".join(lista_ingredienti)
            else:
                dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con gli ingredienti scelti.")
                return {"ingredienti_ricetta": None}
        else:   # se l'utente ha inserito un solo ingrediente, si ricerca su ingrediente principale
            # RICERCA DELL'INGREDIENTE
            result = find_rows(list_ingredienti_word, df_recipe,"ing_principale")
            if len(result) > 0:    
                lista_ing = set(result["ing_principale"].to_list())
                lista_ingredienti = list(lista_ing)
                
                if len(lista_ingredienti) >0 : slot_ingredienti = random.choice(lista_ingredienti)
                else:
                    lista_parole_corrette = correct_words(list_ingredienti_word)
                    print(lista_parole_corrette)
                    result = self.find_rows(lista_parole_corrette, df_recipe,"ing_principale")
                    print(result)
                    lista_ingredienti = list(set(result["ing_principale"].to_list()))
                    if len(lista_ingredienti) >0: slot_ingredienti = random.choice(lista_ingredienti)
                    else:
                        dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con questo ingrediente.")
                        return {"ingredienti_ricetta": None}
            else:
                slot_ingredienti = None
                # dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con questo ingrediente.")
                # return {"ingredienti_ricetta": None}
        
        # SE L'UTENTE DA L'INGREDIENTE E LA PORTATA
        if not slot_portata == "" and slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti} per un {slot_portata}.")
            return {"ingredienti_ricetta": slot_ingredienti, "portata_ricetta": slot_portata}
        # SE L'UTENTE DA L'INGREDIENTE LA PORTATA E IL NUMERO DI PERSONE
        elif not slot_portata == "" and not slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}, per un {slot_portata}, per {slot_num_persone} persone. \n\nRicerca ricetta in corso...")
            return {"ingredienti_ricetta": slot_ingredienti, "portata_ricetta": slot_portata, "num_persone_ricetta": slot_num_persone}
        # SE L'UTENTE DA L'INGREDIENTE E IL NUMERO DI PERSONE
        elif slot_portata == "" and not slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}, per {slot_num_persone} persone.")
            return {"ingredienti_ricetta": slot_ingredienti, "num_persone_ricetta": slot_num_persone}
         # SE L'UTENTE DA L'INGREDIENTE E IL NUMERO DI PERSONE
        elif not slot_portata == "" and slot_ingredienti == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta per un {slot_portata}.")
            return {"ingredienti_ricetta": slot_ingredienti, "num_persone_ricetta": slot_num_persone}
        # SE L'UTENTE DA L'INGREDIENTE
        if not slot_ingredienti == None:
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}.")
            return {"ingredienti_ricetta": slot_ingredienti}

        dispatcher.utter_message(text=f"Inserisca almeno un termine di ricerca, grazie!")
        return {"ingredienti_ricetta": slot_ingredienti}

    def validate_portata_ricetta(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `portata_ricetta` value."""
        print(slot_value)
        if slot_value not in portate_possibili:
            correct_word = difflib.get_close_matches(slot_value,portate_possibili, n=1, cutoff=0.6)
            if not correct_word:       
                dispatcher.utter_message(text=f"Mi dispiace ma non abbiamo questo tipo di portata tra le nostre ricette. Possiamo accettare: {'/'.join(portate_possibili)}.")
                return {"portata_ricetta": None}
            else: 
                slot_value = correct_word[0]
        
        slot_portata = slot_value
        slot_num_persone = tracker.get_slot("num_persone_ricetta")
        slot_ingredienti = tracker.get_slot("ingredienti_ricetta")

        #dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta da {slot_value}.")
        if tracker.get_slot("ingredienti_ricetta") != None and tracker.get_slot("portata_ricetta") != None and tracker.get_slot("num_persone_ricetta") != None:
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}, per un {slot_portata}, per {slot_num_persone} persone. \n\nRicerca ricetta in corso...")
        else:
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta da {slot_portata}.")
        return {"portata_ricetta": slot_value}

    def validate_num_persone_ricetta(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `num_persone_ricetta` value."""
        print(slot_value)
        if slot_value not in num_persone_possibili:
           
            correct_word = difflib.get_close_matches(slot_value,num_persone_possibili, n=1, cutoff=0.6)
            if not correct_word:       
                dispatcher.utter_message(text=f"Mi dispiace ma non abbiamo questo numero di persone. Possiamo accettare: {'/'.join(num_persone_possibili)}.")
                return {"num_persone_ricetta": None}
            else: 
                slot_value = correct_word[0]
        
        try:
            int(slot_value)
        except:
            slot_value = num_translator[slot_value]
        
        slot_num_persone = slot_value
        slot_portata = tracker.get_slot("portata_ricetta")
        slot_ingredienti = tracker.get_slot("ingredienti_ricetta")
         
        if tracker.get_slot("ingredienti_ricetta") != None and tracker.get_slot("portata_ricetta") != None and tracker.get_slot("num_persone_ricetta") != None:
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}, per un {slot_portata}, per {slot_num_persone} persone. \n\nRicerca ricetta in corso...")
        else:
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta per {slot_num_persone} persone.")
        return {"num_persone_ricetta": slot_num_persone}





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
        print(tracker.slots)
        
        # LISTA VUOTA PER LE PAROLE TROVATE DALLA SINTASSI
        list_ricetta_word = []

        # RICERCA DELLE PAROLE CHIAVE (NOMI, AGGETTIVI ECC.) PER LA RICERCA DELL'INGREDIENTE, DELLA PORTATA E DEL NUMERO DI PERSONE
        for token in doc:
            if token.text.lower() in list_parole_da_escludere:
                if token.text.lower() in portate_possibili:
                    nome_ricetta_slot = token.text.lower()
                continue
            if token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'ADV' or token.pos_ == 'ADJ':
                list_ricetta_word.append(token.text.lower())
        
        # PRINTI DELLA SINTASSI DELLE STRINGHE
        print("Lista delle stringhe che ci aiutano a trovare la ricetta: " + str(list_ricetta_word))
        syntax_divisions = [(token.text, token.pos_) for token in doc]
        print("La divisione della sintassi: " + str(syntax_divisions))

        # RICERCA DELL'INGREDIENTE
        result = find_rows(list_ricetta_word, df_recipe,"nome")
        
        if len(result) > 0:
            lista_ricette = list(set(result["nome"].to_list()))
            nome_ricetta_slot = random.choice(lista_ricette)
        else:
            dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta :'(")
            return {"nome_ricetta": None}
        dispatcher.utter_message(text=f"Va bene! Cercherò la ricetta {nome_ricetta_slot}. \n\nRicerca ricetta in corso...")
        return {"nome_ricetta": nome_ricetta_slot}




class ActionCreazioneMenu(Action):
    def name(self) -> Text:
        return "action_ricetta"
    
    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(tracker.slots)
        if tracker.get_slot("nome_ricetta") != None:
            print("Il nome da cercare è: " + str(tracker.get_slot("nome_ricetta")))
            
            nome = tracker.get_slot("nome_ricetta")
            
            ricette = df_recipe[df_recipe['nome'].str.lower().str.contains(nome.lower(),regex=False)]
            
            if len(ricette)==0 : 
                output = "Non ci sono ricette con questo nome."
            else:
                if len(ricette) >= 2: 
                    ricette = ricette.sample(n=2)
                output = buildResponse(ricette)
        
            dispatcher.utter_message(text=output)
            return [AllSlotsReset()]

        elif tracker.get_slot("ingredienti_ricetta") != None or tracker.get_slot("portata_ricetta") != None or tracker.get_slot("num_persone_ricetta") != None:
            print("La ricetta da cercare è con ingredienti, portata o numero di persone")
            ingredienti_slot = tracker.get_slot("ingredienti_ricetta")
            ricette = pd.DataFrame()
            output = ""
            if ingredienti_slot != None:
                ingredienti_slot_l = str(ingredienti_slot).split(", ")
                if len(ingredienti_slot_l) == 1:
                    # ricerca di Meeett
                    ricette = df_recipe[df_recipe['ing_principale'].str.lower().str.contains(ingredienti_slot.lower(),regex=False)]
                else:
                    # ricerca di Simone
                    slot_portata = tracker.get_slot("portata_ricetta")
                    if slot_portata: filter = df_recipe[df_recipe['tipo'].str.lower().str.contains(slot_portata.lower())]
                    else: filter = df_recipe
                    print(ingredienti_slot_l)
                    ricette = filter_by_ingredients(ingredienti_slot_l, filter)
                    print(ricette)
                
            portata_slot = tracker.get_slot("portata_ricetta")
            num_persone_slot = tracker.get_slot("num_persone_ricetta")
            try:
                int(num_persone_slot)
            except:
                num_persone_slot = num_translator[num_persone_slot]
                
            if tracker.get_slot("portata_ricetta") != None:
                ricette = ricette[ricette['tipo'].str.lower().str.contains(portata_slot.lower(),regex=False)]
            if tracker.get_slot("num_persone_ricetta") != None:
                ricette_n_persone = ricette[ricette['n_persone'].astype(str).str.contains(str(num_persone_slot),regex=False)]
                if len(ricette_n_persone)>0 : 
                    ricette = ricette_n_persone
                else:
                    output += "Non è stata trovata una ricetta con il numero di persone scelto. \n"
                    output += "Proverò comunque a cercare una ricetta ;). \n"
                    dispatcher.utter_message(text=output)
                    output = ""
            
            if len(ricette)==0 : 
                output = "Non ci sono ricette con queste caratteristiche."
            else:
                if len(ricette) >= 2: 
                    ricette = ricette.sample(n=2)
                output = buildResponse(ricette)

            dispatcher.utter_message(text=output)
            return [AllSlotsReset()]
                
        return [AllSlotsReset()]


class Action(Action):
    def name(self) -> Text:
        return "action_crea_menu"
    
    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print(tracker.slots)
        if tracker.get_slot("portate") != None:
            portate = list(tracker.get_slot("portate"))
            if "secondo" in portate:
                portate.remove("secondo")
                print(portate)
                dispatcher.utter_message("Quale secondo vuoi?", buttons = buttons)
                return [SlotSet("portate", portate)]
            else:
                ricette = []
                if tracker.get_slot("secondo") != None:
                    portate.append(tracker.get_slot("secondo"))
                for portata in portate:
                    ricette.append(df_recipe[df_recipe["tipo"].str.lower() == str(portata).lower()].sample(n=1))
                response = ""
                for ricetta in ricette:
                    response += buildResponse(ricetta)
                dispatcher.utter_message(text=response)

            return [AllSlotsReset()]
        
        return [AllSlotsReset()]

