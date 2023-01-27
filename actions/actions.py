# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import pandas as pd

pd.set_option('display.max_colwidth', None)


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