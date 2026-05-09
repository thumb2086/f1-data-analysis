# 輪胎策略與衰退分析

## 摘要
- 策略車手數：20
- 最常見策略：HARD(19) -> HARD(17) -> MEDIUM(14) -> SOFT(2)
- 輪胎衰退表聚焦於可用樣本數較足夠的 stint。

## 指標
- drivers: 20
- stints_with_degradation: 48
- compounds:
  - HARD
  - MEDIUM
  - SOFT

## Tyre Strategy

| driver | driver_number | n_stops | stops_label | compounds                      | stint_laps      | total_laps | strategy                                      | final_position |
| ------ | ------------- | ------- | ----------- | ------------------------------ | --------------- | ---------- | --------------------------------------------- | -------------- |
| LEC    | 16            | 1       | 1-stop      | MEDIUM -> HARD                 | [15, 38]        | 53         | MEDIUM(15) -> HARD(38)                        | 1              |
| PIA    | 81            | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [16, 22, 15]    | 53         | MEDIUM(16) -> HARD(22) -> HARD(15)            | 2              |
| NOR    | 4             | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [14, 18, 21]    | 53         | MEDIUM(14) -> HARD(18) -> HARD(21)            | 3              |
| SAI    | 55            | 1       | 1-stop      | MEDIUM -> HARD                 | [19, 34]        | 53         | MEDIUM(19) -> HARD(34)                        | 4              |
| HAM    | 44            | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [15, 22, 16]    | 53         | MEDIUM(15) -> HARD(22) -> HARD(16)            | 5              |
| VER    | 1             | 2       | 2-stop      | HARD -> HARD -> MEDIUM         | [22, 19, 12]    | 53         | HARD(22) -> HARD(19) -> MEDIUM(12)            | 6              |
| RUS    | 63            | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [11, 22, 20]    | 53         | MEDIUM(11) -> HARD(22) -> HARD(20)            | 7              |
| PER    | 11            | 2       | 2-stop      | HARD -> HARD -> MEDIUM         | [23, 12, 18]    | 53         | HARD(23) -> HARD(12) -> MEDIUM(18)            | 8              |
| ALB    | 23            | 1       | 1-stop      | MEDIUM -> HARD                 | [17, 36]        | 53         | MEDIUM(17) -> HARD(36)                        | 9              |
| MAG    | 20            | 1       | 1-stop      | MEDIUM -> HARD                 | [14, 39]        | 53         | MEDIUM(14) -> HARD(39)                        | 10             |
| ALO    | 14            | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [12, 23, 18]    | 53         | MEDIUM(12) -> HARD(23) -> HARD(18)            | 11             |
| COL    | 43            | 1       | 1-stop      | MEDIUM -> HARD                 | [16, 37]        | 53         | MEDIUM(16) -> HARD(37)                        | 12             |
| RIC    | 3             | 1       | 1-stop      | MEDIUM -> HARD                 | [11, 42]        | 53         | MEDIUM(11) -> HARD(42)                        | 13             |
| OCO    | 31            | 1       | 1-stop      | HARD -> MEDIUM                 | [31, 21]        | 52         | HARD(31) -> MEDIUM(21)                        | 14             |
| GAS    | 10            | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [10, 20, 22]    | 52         | MEDIUM(10) -> HARD(20) -> HARD(22)            | 15             |
| BOT    | 77            | 1       | 1-stop      | HARD -> MEDIUM                 | [33, 19]        | 52         | HARD(33) -> MEDIUM(19)                        | 16             |
| HUL    | 27            | 2       | 2-stop      | MEDIUM -> HARD -> HARD         | [5, 27, 20]     | 52         | MEDIUM(5) -> HARD(27) -> HARD(20)             | 17             |
| ZHO    | 24            | 1       | 1-stop      | MEDIUM -> HARD                 | [15, 37]        | 52         | MEDIUM(15) -> HARD(37)                        | 18             |
| STR    | 18            | 3       | 3-stop      | HARD -> HARD -> MEDIUM -> SOFT | [19, 17, 14, 2] | 52         | HARD(19) -> HARD(17) -> MEDIUM(14) -> SOFT(2) | 19             |
| TSU    | 22            | 0       | 0-stop      | HARD                           | [7]             | 7          | HARD(7)                                       | 20             |

## Tyre Degradation

| driver | stint | compound | degradation_rate | intercept | laps_analyzed | r2    |
| ------ | ----- | -------- | ---------------- | --------- | ------------- | ----- |
| RIC    | 1     | MEDIUM   | -0.135           | 87.037    | 9             | 0.641 |
| ALO    | 1     | MEDIUM   | -0.128           | 87.098    | 10            | 0.705 |
| BOT    | 2     | MEDIUM   | -0.113           | 86.21     | 18            | 0.517 |
| ZHO    | 1     | MEDIUM   | -0.1             | 87.757    | 13            | 0.15  |
| RUS    | 1     | MEDIUM   | -0.096           | 86.018    | 9             | 0.551 |
| HAM    | 2     | HARD     | -0.088           | 84.942    | 20            | 0.795 |
| RUS    | 3     | HARD     | -0.084           | 83.795    | 19            | 0.41  |
| MAG    | 1     | MEDIUM   | -0.064           | 86.651    | 12            | 0.32  |
| NOR    | 3     | HARD     | -0.056           | 83.349    | 20            | 0.248 |
| NOR    | 2     | HARD     | -0.055           | 84.347    | 16            | 0.161 |
| RUS    | 2     | HARD     | -0.054           | 84.999    | 20            | 0.228 |
| MAG    | 2     | HARD     | -0.046           | 85.517    | 38            | 0.635 |

## Compound Comparison

| Driver | Compound | avg_laptime | min_laptime | max_laptime | std_laptime | laps | avg_tyre_life |
| ------ | -------- | ----------- | ----------- | ----------- | ----------- | ---- | ------------- |
| ALB    | HARD     | 84.795      | 83.918      | 86.282      | 0.529       | 35   | 19            |
| ALB    | MEDIUM   | 86.062      | 85.468      | 87.011      | 0.426       | 15   | 9             |
| ALO    | HARD     | 84.372      | 82.944      | 85.832      | 0.802       | 38   | 12.553        |
| ALO    | MEDIUM   | 86.139      | 85.693      | 87.236      | 0.461       | 10   | 7.5           |
| BOT    | HARD     | 86.671      | 85.804      | 88.377      | 0.614       | 31   | 18            |
| BOT    | MEDIUM   | 84.91       | 83.609      | 86.704      | 0.84        | 18   | 11.5          |
| COL    | HARD     | 84.875      | 83.728      | 85.979      | 0.438       | 36   | 19.5          |
| COL    | MEDIUM   | 86.65       | 86.057      | 87.845      | 0.484       | 14   | 8.5           |
| GAS    | HARD     | 85.096      | 83.755      | 87.191      | 0.795       | 39   | 11.308        |
| GAS    | MEDIUM   | 86.435      | 85.82       | 87.148      | 0.4         | 8    | 5.5           |
| HAM    | HARD     | 83.399      | 81.512      | 85.703      | 0.963       | 35   | 10.429        |
| HAM    | MEDIUM   | 85.24       | 84.771      | 86.043      | 0.425       | 13   | 8             |
| HUL    | HARD     | 84.937      | 83.275      | 87.809      | 1.034       | 44   | 12.705        |
| HUL    | MEDIUM   | 86.829      | 86.434      | 87.512      | 0.594       | 3    | 3             |
| LEC    | HARD     | 83.625      | 83.226      | 84.27       | 0.249       | 37   | 20            |
| LEC    | MEDIUM   | 84.873      | 84.362      | 85.606      | 0.428       | 13   | 8             |
| MAG    | HARD     | 84.581      | 83.437      | 86.533      | 0.637       | 38   | 20.5          |
| MAG    | MEDIUM   | 86.171      | 85.785      | 87.205      | 0.408       | 12   | 7.5           |
| NOR    | HARD     | 83.202      | 81.432      | 85.585      | 0.864       | 36   | 10.611        |
| NOR    | MEDIUM   | 84.825      | 84.391      | 85.458      | 0.357       | 12   | 7.5           |
| OCO    | HARD     | 86.331      | 85.369      | 87.519      | 0.447       | 29   | 16            |
| OCO    | MEDIUM   | 84.944      | 84.343      | 86.111      | 0.483       | 20   | 11.5          |
| PER    | HARD     | 84.925      | 83.473      | 86.411      | 0.859       | 31   | 10.226        |
| PER    | MEDIUM   | 83.722      | 82.971      | 86.243      | 0.801       | 17   | 10            |
| PIA    | HARD     | 83.069      | 81.943      | 84.602      | 0.672       | 34   | 10.265        |
| PIA    | MEDIUM   | 84.69       | 84.077      | 85.261      | 0.355       | 14   | 8.5           |
| RIC    | HARD     | 85.022      | 84.219      | 86.122      | 0.386       | 41   | 23            |
| RIC    | MEDIUM   | 86.226      | 85.713      | 87.177      | 0.462       | 9    | 6             |
| RUS    | HARD     | 83.647      | 82.036      | 85.504      | 1.03        | 39   | 11.256        |
| RUS    | MEDIUM   | 85.443      | 85.046      | 86.055      | 0.353       | 9    | 6             |
| SAI    | HARD     | 83.768      | 83.219      | 85.113      | 0.466       | 33   | 18            |
| SAI    | MEDIUM   | 85.146      | 84.642      | 85.731      | 0.333       | 17   | 10            |
| STR    | HARD     | 85.738      | 84.437      | 88.342      | 0.994       | 32   | 11            |
| STR    | MEDIUM   | 84.277      | 83.427      | 86.104      | 0.891       | 12   | 8.5           |
| STR    | SOFT     | 82.232      | 82.232      | 82.232      | -           | 1    | 2             |
| TSU    | HARD     | 88.223      | 86.198      | 92.241      | 2.409       | 5    | 5             |
| VER    | HARD     | 84.525      | 83.424      | 86.17       | 0.922       | 37   | 10.811        |
| VER    | MEDIUM   | 82.778      | 81.745      | 83.711      | 0.512       | 11   | 7             |
| ZHO    | HARD     | 85.938      | 85.092      | 87.64       | 0.645       | 36   | 20.5          |
| ZHO    | MEDIUM   | 86.854      | 85.942      | 89.256      | 1.008       | 13   | 9             |

## 詳細資料
- top_strategy:
  - driver: LEC
  - driver_number: 16
  - n_stops: 1
  - stops_label: 1-stop
  - compounds: MEDIUM -> HARD
  - stint_laps:
    - 15
    - 38
  - total_laps: 53
  - strategy: MEDIUM(15) -> HARD(38)
  - final_position: 1
