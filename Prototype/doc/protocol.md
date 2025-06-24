# Glasgow Coma Scale (GCS) Calculation Protocol

## 1. Protocol Start

The protocol begins when the **"Estimate GCS" button** is pressed in the application GUI, after selecting the inference type (**local** or **remote**).

## 2. Data Sampling

From this point, the following data are collected:

- **Physiological Data**:
  - Eye State: open/closed/partially closed
  - Eye Movement: moving/stationary
  - Heart rate: average frequency

- **User Questions** (Answers to **3 binary yes/no questions**, acquired via Whisper voice recognition):
  1. "Can you hear me?"
  2. "Can you open your eyes?"
  3. "Can you move your eyes right now?"

- **System Metrics**:
  - FPS
  - CPU, Memory, Swap usage
  - Whisper inference time (single or total)

## 3. Protocol End

After the three questions and data collection:

- Data collection **ends**
- The **GCS score** is calculated using the specified logic
- Collected data and inference type are saved
