# Monza 2024 baseline predictions

This artifact contains an explainable rule-based baseline for three outputs per driver:
Top 3 / Top 10 / DNF class, start-finish gain band, and one-stop vs two-stop strategy.

## Summary
- Drivers: 20
- Predicted Top 3: 3
- Predicted Top 10: 7
- Predicted DNF bucket: 10
- Predicted One-stop: 10
- Predicted Two-stop: 10

## Driver predictions
| rank | driver | full_name        | team_name       | predicted_result_class | predicted_gain_band | predicted_strategy |
| ---- | ------ | ---------------- | --------------- | ---------------------- | ------------------- | ------------------ |
| 1    | NOR    | Lando Norris     | McLaren         | Top 3                  | Hold                | Two-stop           |
| 2    | PIA    | Oscar Piastri    | McLaren         | Top 3                  | Hold                | Two-stop           |
| 3    | LEC    | Charles Leclerc  | Ferrari         | Top 3                  | Gain 1-4            | One-stop           |
| 4    | RUS    | George Russell   | Mercedes        | Top 10                 | Loss 1-4            | Two-stop           |
| 5    | SAI    | Carlos Sainz     | Ferrari         | Top 10                 | Hold                | One-stop           |
| 6    | HAM    | Lewis Hamilton   | Mercedes        | Top 10                 | Hold                | Two-stop           |
| 7    | VER    | Max Verstappen   | Red Bull Racing | Top 10                 | Hold                | Two-stop           |
| 8    | PER    | Sergio Perez     | Red Bull Racing | Top 10                 | Hold                | Two-stop           |
| 9    | ALB    | Alexander Albon  | Williams        | Top 10                 | Hold                | One-stop           |
| 10   | ALO    | Fernando Alonso  | Aston Martin    | Top 10                 | Gain 1-4            | Two-stop           |
| 11   | HUL    | Nico Hulkenberg  | Haas F1 Team    | DNF                    | Loss 1-4            | Two-stop           |
| 12   | RIC    | Daniel Ricciardo | RB              | DNF                    | Hold                | One-stop           |
| 13   | MAG    | Kevin Magnussen  | Haas F1 Team    | DNF                    | Hold                | One-stop           |
| 14   | GAS    | Pierre Gasly     | Alpine          | DNF                    | Hold                | Two-stop           |
| 15   | OCO    | Esteban Ocon     | Alpine          | DNF                    | Hold                | One-stop           |
| 16   | COL    | Franco Colapinto | Williams        | DNF                    | Gain 1-4            | One-stop           |
| 17   | STR    | Lance Stroll     | Aston Martin    | DNF                    | Hold                | Two-stop           |
| 18   | BOT    | Valtteri Bottas  | Kick Sauber     | DNF                    | Gain 1-4            | One-stop           |
| 19   | ZHO    | Guanyu Zhou      | Kick Sauber     | DNF                    | Gain 1-4            | One-stop           |
| 20   | TSU    | Yuki Tsunoda     | RB              | DNF                    | Loss 1-4            | One-stop           |

## Notes
- Result class is a transparent ranking bucket built from grid, pace, consistency, degradation and team proxy scores.
- Gain band is derived from predicted finish rank minus grid position.
- Strategy is based on stint count, longest stint length, hard-tyre share and tyre degradation slope.
- DNF is used as the coarse lower bucket for drivers outside the top 10 in this baseline.