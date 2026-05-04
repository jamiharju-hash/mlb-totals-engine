# Statcast + FG/BR -malliputken tekninen speksi

Tämä dokumentti kuvaa end-to-end MLB O/U + ML -malliputken, joka hyödyntää Statcast-, FanGraphs/Baseball Reference-, sää-, odds- ja tuomaridataa.

## 1) Datalähteet

### 1.1 Pelidata: Statcast + FG/BR
- Pelikohtaiset tapahtumat, syöttäjä- ja lyöjämetriikat.
- Joukkue- ja pelaajatasojen aggregaatiot (L7/L14/L30).

### 1.2 Sää-API
- Tuulen suunta/nopeus (wind speed + vector).
- Lämpötila (°C/°F) ja mahdollinen kosteus/ilmanpaine.
- Stadium-kohtainen weather join pelin aloitushetkeen.

### 1.3 Odds-API
- Avauslinjat (opening) ja sulkeutumislinjat (closing):
  - Moneyline (ML)
  - Over/Under (O/U)
  - Run line
- Usean bookkerin feed + mahdollinen best-price normalisointi.

### 1.4 Tuomaridata
- Umpire over/under bias historia.
- Strike zone -käyttäytymisen johdetut metriikat.

## 2) Tietokantamalli (dim / fact)

### 2.1 `dim_games`
- `game_id`
- `game_date`
- `home_team`, `away_team`
- `park_id`, `scheduled_start_utc`

### 2.2 `dim_odds`
- `game_id`
- `bookmaker`
- `opening_ml_home`, `opening_ml_away`
- `closing_ml_home`, `closing_ml_away`
- `opening_ou`, `closing_ou`
- `opening_runline`, `closing_runline`

### 2.3 `fact_pitcher_boxscore`
- `game_id`, `pitcher_id`, `team`
- `xFIP`, `K_pct`, `BB_pct`
- rolling-ikkunat: `xFIP_L14`, `K_pct_L14`, `BB_pct_L14`

### 2.4 `fact_team_boxscore`
- `game_id`, `team`
- `runs_scored`, `errors`
- rolling-ikkunat: `bullpen_ERA_L7`, `wRC_plus_vs_LHP`, `wRC_plus_vs_RHP`

## 3) Feature engineering

### 3.1 Feature-matriisi `X`
Esimerkkifeatureita:
- `home_pitcher_xFIP_L14`
- `away_bullpen_ERA_L7`
- `home_wRC_plus_vs_LHP`
- `weather_wind_speed`
- `weather_temperature`
- `umpire_over_under_bias`
- `opening_ML_line`

### 3.2 Esikäsittely
- Puuttuvien arvojen imputointi (median/forward-fill mallikohtaisesti).
- Kategoristen muuttujien koodaus (team, park, umpire).
- `StandardScaler` jatkuville featureille.
- Vuototurvallinen fit-transform vain treenijoukolla.

## 4) Mallit

### 4.1 Neuroverkko (MLP) - luokittelu
- Tavoite: kotivoitto todennäköisyys `P(y=1)`.
- Output: sigmoid, loss: binary cross-entropy.
- Kalibrointi (Platt/isotonic) ennen EV-laskentaa.

### 4.2 Neuroverkko (MLP) - regressio
- Tavoite: juoksumäärät (esim. total runs / team runs).
- Output: jatkuva ennuste.
- Loss: MAE/MSE/Huber malliversiosta riippuen.

## 5) EV-analyysi ja vedonlyöntipäätös

### 5.1 Reilu kerroin
- `Fair Odds = 1 / P`
- Esimerkki: `P = 0.58` -> `Fair Odds = 1.72`

### 5.2 Edge-laskelma
- Jos bookmakerin kerroin > reilu kerroin, edge > 0.
- Esimerkki: bookkeri 1.85 vs fair 1.72 -> `EV > 0`.

### 5.3 Päivän vetosuositus
Jokaiselle kohteelle tallennetaan:
- kohde
- markkina (ML / O/U / RL)
- kerroin
- arvioitu EV
- luottamusväli
- panoskoko (Kelly-fraktio capilla)

## 6) Operointi

### 6.1 Aamu-cronjob
- Päivittäinen ingest + feature update + inference.
- Tulosten kirjoitus dashboard-/signaali-tauluihin.

### 6.2 Panostuslogiikka
- Kelly-kriteeri (fractional Kelly, esim. 0.25x–0.5x).
- Riskikatot per päivä/markkina.

## 7) Minimi-MVP toteutusjärjestys
1. `dim_games` + `dim_odds` + kaksi fact-taulua.
2. Ensimmäinen feature store (L7/L14 rolling + weather + opening line).
3. ML-luokittelumalli (home win) + kalibrointi.
4. EV-laskenta + ranking + daily recommendations.
5. Regressiomalli juoksumäärille (O/U tarkennus).
