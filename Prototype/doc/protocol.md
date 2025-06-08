# Protocollo di Calcolo del Glasgow Coma Scale (GCS)

## 1. Avvio del Protocollo

Il protocollo inizia con la **pressione del tasto "Calcolare GCS"** sulla GUI dell’applicazione, dopo aver specificato il tipo di inferenza (**locale** o **remota**). 

## 2. Campionamento Dati

A partire da questo momento, vengono campionati i seguenti dati:

- **Dati fisiologici**:
  - Stato Occhi: apertura/chiusura/chiusura parziale
  - Movimento Occhi: movimento/stazionari
  - Heart rate: frequenza media

- **Domande all’utente** (Risposte a **3 domande binarie** (sì/no), acquisite tramite riconoscimento vocale Whisper):
  1. "Can you hear me?"
  2. "Do you know your name?" / "Can you open your eyes?"
  3. "Can you move your eyes right now?"

  _Varianti possibili:_
  - "Can you hear me?"
  - "Can you move?"
  - "Are you okay?"

- **Metriche di sistema**:
  - FPS
  - CPU, Memoria, Swap
  - Tempo per inferenza Whisper (singola o totale)


## 3. Fine del Protocollo

Alla fine delle tre domande e del relativo campionamento:

- Il sistema **termina la raccolta dati**
- Viene calcolato lo **score GCS** utilizzando la logica riportata successivamente
- Il sistema salva i dati raccolti e il tipo di inferenza

### Algoritmo di Calcolo GCS

```python
# Stato occhi
eye_state = Counter(self.eyes_status_list).most_common(1)[0][0]
if eye_state == "Open":
    eye_score = 3
elif eye_state == "Slightly Closed":
    eye_score = 2
elif eye_state == "Closed":
    eye_score = 1
else:
    eye_score = 0  # Stato sconosciuto

# Movimento
movement_state = Counter(self.movement_status_list).most_common(1)[0][0]
if movement_state == "Moving":
    movement_score = 2
elif movement_state == "Stationary":
    movement_score = 1
else:
    movement_score = 0

# Heart rate
heart_rate = statistics.mean(self.heart_rate_status_list)
if 50 <= heart_rate < 80:
    hr_score = 3
elif 80 <= heart_rate < 100:
    hr_score = 2
elif heart_rate >= 100:
    hr_score = 1
else:
    hr_score = 0

# Risposte utente
user_answer_score = Counter(self.user_answers_list)[1]

# Calcolo GCS totale
gcs_score = eye_score + movement_score + hr_score + user_answer_score
```
