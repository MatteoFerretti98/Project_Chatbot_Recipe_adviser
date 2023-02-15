# Project_Chatbot_Recipe_adviser

## Team

**• [Di Rado Simone](https://github.com/Simdr98)** \
**• [Ferretti Matteo](https://github.com/MatteoFerretti98)** \
**• [Leli Samuele](https://github.com/samueleleli)**

## Obiettivo del Progetto

L'obiettivo del progetto è stato quello di realizzare un ChatBot utilizzando il software Rasa.

## Avvio
**• Clonare la seguente repository da terminale e spostarsi all'interno della cartella**
```bash
git clone https://github.com/MatteoFerretti98/Project_Chatbot_Recipe_adviser.git
```
**• Installare la versione 3 di Python**
**• Creare un ambiente virtuale e installazione delle dipendenze tramite il file requirements.txt:**
Questo è possibile farlo utilizzando 2 modi:

  1) Utilizzando anaconda:
  ```bash
  conda create --name <environment_name> --file ./requirements.txt
  ```
  o semplicemente se l'environment è già stato creato:
  ```bash
  conda install --file ./requirements.txt
  ```
  2) Utilizzando un v-env manuale (virtual-environment):
  ```bash
  py -3 -m venv .venv
  .venv\scripts\activate
  pip install -r ./requirements.txt
  ```

**•Creare un file chiamato ".env" con questa struttura:** (sostituire 'secretkey' con la private key di SERPAPI) 
Questo è servito per poter cercare le immagini delle ricerche da google
```bash
SERPAPI_KEY=secretkey
```
**• Fare il training del modello:**
```bash
rasa train
```

**• Avviare il chatbot:**

In questa fase si potrebbe avere la necessità di avere fino a un massimo di 3 terminali che devono rimanere attivi fino a quando il bot è operativo.

Digitare il comando nel **terminale 1**:
```bash
rasa run actions
```
Dopodiché ci sono 2 opzioni:
  - Utilizzarlo tramite telegram:
  In questo caso bisogna digitare il comando nel **terminale 2**: 
```bash
.\ngrok.exe http 5005
```
A questo punto verrà dato in output un URL che bisogna inserire all'interno del file "credentials.yml" nella proprietà "webhook_url":

Esempio di url in output: https://dc9e-89-46-12-180.eu.ngrok.io

Url da inserire nella proprietà "webhook_url": "https://dc9e-89-46-12-180.eu.ngrok.io/webhooks/telegram/webhook"

Eseguite queste operazioni, si può lanciare il comando nel **terminale 3**: 

```bash
rasa run
```
  - Utilizzarlo da linea di comando:
  In questo caso serve semplicemente lanciare il seguente comando nel **terminale 2**: (N.B. le immagini non saranno visualizzate):
  
```bash
rasa shell
```

