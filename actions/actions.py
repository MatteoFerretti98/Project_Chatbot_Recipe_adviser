# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import json
from pathlib import Path
from typing import Any, Text, Dict, List
import requests
from rasa_sdk.events import SlotSet

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.knowledge_base.storage import InMemoryKnowledgeBase
from rasa_sdk.knowledge_base.actions import ActionQueryKnowledgeBase
from rasa_sdk.events import SlotSet

class ActionFindInfo(Action):
    
    def name(self) -> Text:
        return "action_find_info"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = str(tracker.get_slot('country'))
        r=requests.get(url='https://restcountries.com/v3.1/name/{}'.format(name.lower()))
        
        
        if r.status_code == 200 :
            data = r.json()
            flag=list(data[0]['flags'].values())[0]
            capital = data[0]['capital'][0]#capitale 
            moneta= list(data[0]['currencies'].values())[0]['name'] #moneta  
            simbolo_moneta= list(data[0]['currencies'].values())[0]['symbol'] #simbolo
            subregion =data[0]['subregion'] # subregion
            area=data[0]['area'] #area
            population= data[0]['population'] #population
            output="{} is a state located in {}, the population number is {}, the area is {}, its capital is {}. The currency is {}, its symboly is {} and you can see its flag at this link {}.".format(name,subregion,population,area,capital,moneta,simbolo_moneta,flag)
        else:
            output = "I do not know anything about, what a mistery!? Are you sure it is correctly spelled?"
        dispatcher.utter_message(text=output)
        return []

class ActionFindCapital(Action):
    
    def name(self) -> Text:
        return "action_find_capital"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot('country')
        r=requests.get(url='https://restcountries.com/v3.1/name/{}'.format(name.lower()))
         

        if r.status_code == 200:
            data = r.json()
            capital = data[0]['capital'][0]#capitale
            output="The capital of {} is {}.".format(name,capital)
        else:
            output = "I do not know anything about , what a mistery!? Are you sure it is correctly spelled?"
            
        dispatcher.utter_message(text=output)
        return []

class MyFallback(Action):
    
    def name(self) -> Text:
        return "action_my_fallback"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response = "utter_fallback")
        return []