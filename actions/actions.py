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

# Load the spaCy model for the Italian language
nlp = spacy.load("it_core_news_sm")



pd.set_option('display.max_colwidth', None)

def all_lower(my_list):
    return [x.lower() for x in my_list]

#df_ingredients = pd.read_csv('./actions/dataset_ricette/ingredienti.csv')
df_recipe = pd.read_csv('./actions/dataset_ricette/ricette.csv')
ingredienti_possibili = df_recipe["ing_principale"].tolist()

ingredienti_possibili = list(set(ingredienti_possibili))
ingredienti_possibili = all_lower(ingredienti_possibili)

single_word_list = []
for phrase in ingredienti_possibili:
    words = phrase.split()
    for word in words:
        single_word_list.append(word)
single_word_list = list(set(single_word_list))

#with open("lookup_table_ingredienti.txt", "w") as file:
#        for string in ingredienti_possibili:
#            file.write(string + "\n")
#print(len(ingredienti_possibili))

num_persone_possibili_int = df_recipe["n_persone"].tolist()
num_persone_possibili = [str(numero) for numero in num_persone_possibili_int]
num_persone_possibili = list(set(num_persone_possibili))
#print(num_persone_possibili)


portate_possibili = df_recipe["tipo"].tolist()
portate_possibili = list(set(portate_possibili))
portate_possibili = all_lower(portate_possibili)
#print(portate_possibili)


list_parole_da_escludere = df_recipe["tipo"].tolist()
list_parole_da_escludere = list(set(list_parole_da_escludere))
list_parole_da_escludere = all_lower(list_parole_da_escludere)



class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")

        return []


class MyFallback(Action):
    
    def name(self) -> Text:
        return "action_my_fallback"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        dispatcher.utter_message(response = "utter_fallback")
        return []



class ValidateRicettaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_ricetta_form"
    

    def find_rows(self, strings, df):
            result = df
            for string in strings:
                result = result[result["ing_principale"].str.lower().str.contains(string.lower())]
            return result

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

        doc = nlp(tracker.latest_message["text"])



        list_ingredienti_word = []
        list_parole_da_escludere.append('ricetta')
        list_parole_da_escludere.append('ingrediente')
        list_parole_da_escludere.append('ingredienti')
        list_parole_da_escludere.append('persone')

        for token in doc:
            if token.text.lower() in list_parole_da_escludere:
                if token.text.lower() in portate_possibili:
                    slot_portata = token.text.lower()
                continue
            if token.pos_ == 'NUM':
                slot_num_persone = token.text.lower()
            if token.pos_ == 'NOUN' or token.pos_ == 'PROPN' or token.pos_ == 'ADV' or token.pos_ == 'ADJ':
                list_ingredienti_word.append(token.text.lower())

        #Print della sintassi delle stringhe
        print("Lista delle stringhe che ci aiutano a trovare l'ingrediente: " + str(list_ingredienti_word))
        syntax_divisions = [(token.text, token.pos_) for token in doc]
        print("La divisione della sintassi: " + str(syntax_divisions))
        
        
        result = self.find_rows(list_ingredienti_word, df_recipe)
        lista_ingredienti = list(set(result["ing_principale"].to_list()))
        if len(lista_ingredienti) >0: slot_ingredienti = random.choice(lista_ingredienti)
        else:
            # CORREZIONE DELLE STRINGHE
            lista_parole_corrette = []
            for ingredienti_singoli_word in list_ingredienti_word:
                
                correct_word = difflib.get_close_matches(ingredienti_singoli_word, single_word_list, n=1, cutoff=0.6)
                if correct_word:
                    lista_parole_corrette.append(correct_word[0])
            
            result = self.find_rows(lista_parole_corrette, df_recipe)
            lista_ingredienti = list(set(result["ing_principale"].to_list()))
            if len(lista_ingredienti) >0: slot_ingredienti = random.choice(lista_ingredienti)
            else:
                dispatcher.utter_message(text=f"Mi dispiace ma non ho trovato nessuna ricetta con questo ingrediente.")
                return {"ingredienti_ricetta": None}

            
        if not slot_portata == "" and slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti} per un {slot_portata}.")
            return {"ingredienti_ricetta": slot_ingredienti, "portata_ricetta": slot_portata}
        elif not slot_portata == "" and not slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}, per un {slot_portata}, per {slot_num_persone} persone.")
            return {"ingredienti_ricetta": slot_ingredienti, "portata_ricetta": slot_portata, "num_persone_ricetta": slot_num_persone}
        elif slot_portata == "" and not slot_num_persone == "":
            dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}, per {slot_num_persone} persone.")
            return {"ingredienti_ricetta": slot_ingredienti, "num_persone_ricetta": slot_num_persone}
        dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta con {slot_ingredienti}.")
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
            dispatcher.utter_message(text=f"Mi dispiace ma non abbiamo questo tipo di portata tra le nostre ricette. Possiamo accettare: {'/'.join(portate_possibili)}.")
            return {"portata_ricetta": None}
        dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta da {slot_value}.")
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
            dispatcher.utter_message(text=f"Mi dispiace, ma non abbiamo ricette per il numero di persone richiesto. Ecco i numeri di persone che accettiamo: {'/'.join(num_persone_possibili)}.")
            return {"num_persone_ricetta": None}
        dispatcher.utter_message(text=f"Va bene! Cercherò una ricetta per {slot_value} persone.")
        return {"num_persone_ricetta": slot_value}




class ActionRicercaPerNome(Action):
    def name(self) -> Text:
        return "action_ricercaNome"
    
    def buildResponse(self,df):
        output = ""
        for index, row in df.iterrows():
            output += "\n\n"
            output += "Nome: " + row["nome"] + "\n"
            output += "Tipo di piatto: " + row["tipo"] + "\n"
            output += "Ingrediente principale: " + str(row["ing_principale"]) + "\n"
            output += "Numero di persone: " + str(row["n_persone"]) + "\n"
            output += "Note: " + str(row["note"]) + "\n"
            output += "Preparazione: " + str(row["preparazione"])
        
        return output

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        df = pd.read_csv('./actions/dataset_ricette/ricette.csv')
        nome_completo = list(tracker.get_latest_entity_values('nome_ricetta'))
        nome = str(tracker.get_slot('nome_ricetta'))
        for nomi in nome_completo:
            print(nomi)
        ricette = df[df['nome'].str.lower().str.contains(nome.lower())]
        
        if len(ricette)==0 : 
            output = "Non ci sono ricette con questo nome"
        else:
            if len(ricette) > 2: 
                ricette = ricette.sample(n=3)
            output = self.buildResponse(ricette)
    
        dispatcher.utter_message(text=output)
        return []