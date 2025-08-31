# Air Quality Insights

## 🌐 Background

The challenge of energy pollution and climate action arises from the global dependency on fossil fuels, which are the primary contributors to greenhouse gas emissions. The combustion of coal, oil, and natural gas for energy production releases carbon dioxide and other harmful pollutants into the atmosphere, accelerating climate change and damaging ecosystems. As energy demand surges due to population growth and industrial development, the environmental impact intensifies. This challenge necessitates innovative solutions to transition towards cleaner energy sources, enhance energy efficiency, and implement sustainable practices. Tackling energy pollution is vital not only for mitigating climate change but also for fostering healthier communities and ensuring long-term environmental sustainability.

### 🗂️ Dataset

Three distinct datasets will be provided:

- Measurement data:
  - Variables:
    - `Measurement date`
    - `Station code`
    - `Latitude`
    - `Longitude`
    - `SO2`
    - `NO2`
    - `O3`
    - `CO`
    - `PM10`
    - `PM2.5`

- Instrument data

  - Variables:
    - `Measurement date`
    - `Station code`
    - `Item code`
    - `Average value`
    - `Instrument status` : Status of the measuring instrument when the sample was taken.
    ```json
    {
      "0": "Normal",
      "1": "Need for calibration",
      "2": "Abnormal",
      "4": "Power cut off",
      "8": "Under repair",
      "9": "Abnormal data"
    }
    ```

- Pollutant data
- Variables:
  - `Item code`
  - `Item name`
  - `Unit of measurement`
  - `Good`
  - `Normal`
  - `Bad`
  - `Very bad`

### 📊 Data Processing

Perform comprehensive data processing, including filtering, normalization, and handling missing values.

Afterwards, develop two machine learning models:

- **Forecast Model:** Predict hourly air quality for specified periods, assuming no measurement errors.

- **Instrument Status Model:** Detect and classify failures in measurement instruments.

## 🎯 Tasks

This challenge will include three tasks: an initial exploratory data analysis task with questions, followed by two model creation tasks.

#### **Task 1:** Answer the following questions about the given datasets:

**IMPORTANT** Answer the following questions considering only measurements with the value tagged as "Normal" (code 0):

- **Q1:** Average daily SO2 concentration across all districts over the entire period. Give the station average. Provide the answer with 5 decimals.
- **Q2:** Analyse how pollution levels vary by season. Return the average levels of CO per season at the station 209. (Take the whole month of December as part of winter, March as spring, and so on.) Provide the answer with 5 decimals.
- **Q3:** Which hour presents the highest variability (Standard Deviation) for the pollutant O3? Treat all stations as equal.
- **Q4:** Which is the station code with more measurements labeled as "Abnormal data"?
- **Q5:** Which station code has more "not normal" measurements (!= 0)?
- **Q6:** Return the count of `Good`, `Normal`, `Bad` and `Very bad` records for all the station codes of PM2.5 pollutant.

#### **Task 2:** Develop the forecasting model :

- Predict hourly pollutant concentrations for the following stations and periods, assuming error-free measurements:

```
Station code: 206 | pollutant: SO2   | Period: 2023-07-01 00:00:00 - 2023-07-31 23:00:00
Station code: 211 | pollutant: NO2   | Period: 2023-08-01 00:00:00 - 2023-08-31 23:00:00
Station code: 217 | pollutant: O3    | Period: 2023-09-01 00:00:00 - 2023-09-30 23:00:00
Station code: 219 | pollutant: CO    | Period: 2023-10-01 00:00:00 - 2023-10-31 23:00:00
Station code: 225 | pollutant: PM10  | Period: 2023-11-01 00:00:00 - 2023-11-30 23:00:00
Station code: 228 | pollutant: PM2.5 | Period: 2023-12-01 00:00:00 - 2023-12-31 23:00:00
```

#### **Task 3:** Detect anomalies in data measurements

Detect instrument anomalies for the following stations and periods:

```
Station code: 205 | pollutant: SO2   | Period: 2023-11-01 00:00:00 - 2023-11-30 23:00:00
Station code: 209 | pollutant: NO2   | Period: 2023-09-01 00:00:00 - 2023-09-30 23:00:00
Station code: 223 | pollutant: O3    | Period: 2023-07-01 00:00:00 - 2023-07-31 23:00:00
Station code: 224 | pollutant: CO    | Period: 2023-10-01 00:00:00 - 2023-10-31 23:00:00
Station code: 226 | pollutant: PM10  | Period: 2023-08-01 00:00:00 - 2023-08-31 23:00:00
Station code: 227 | pollutant: PM2.5 | Period: 2023-12-01 00:00:00 - 2023-12-31 23:00:00
```

### 💫 Guides

- Study and explore the datasets thoroughly.
- Handle missing or erroneous values.
- Normalize and scale the data.
- Implement feature engineering to improve model accuracy.