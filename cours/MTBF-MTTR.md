Parfait 👌 ! Ce sont deux indicateurs classiques, à la fois en **industrie** (maintenance) et en **IT** (fiabilité des systèmes).

---

# 🔹 MTBF — *Mean Time Between Failures*

👉 **Temps moyen entre deux pannes**.

* C’est une mesure de **fiabilité** : combien de temps un système fonctionne en moyenne avant de tomber en panne.
* Plus le MTBF est grand, plus l’équipement est fiable.

📐 Formule :

$$
MTBF = \frac{\text{Temps total de fonctionnement}}{\text{Nombre de pannes}}
$$

### Exemple :

* Une machine fonctionne 1000 heures sur un trimestre.
* Elle est tombée en panne 5 fois.
  👉 MTBF = 1000 ÷ 5 = **200 heures** entre deux pannes.

---

# 🔹 MTTR — *Mean Time To Repair*

👉 **Temps moyen pour réparer** après une panne.

* C’est une mesure de **maintenabilité** : combien de temps en moyenne il faut pour remettre un système en état après une panne.
* Plus le MTTR est petit, plus la maintenance est efficace.

📐 Formule :

$$
MTTR = \frac{\text{Temps total d’indisponibilité}}{\text{Nombre de pannes}}
$$

### Exemple :

* 5 pannes ont causé au total 50h d’arrêt.
  👉 MTTR = 50 ÷ 5 = **10 heures** par panne en moyenne.

---

# 🔹 Lien entre les deux

On combine souvent MTBF & MTTR pour évaluer la **disponibilité** d’un système :

$$
\text{Disponibilité} = \frac{MTBF}{MTBF + MTTR}
$$

### Exemple :

* MTBF = 200h
* MTTR = 10h
  👉 Disponibilité = 200 ÷ (200 + 10) ≈ **95,2 %**

---

# 🔹 Utilisation

* **Industrie / IoT** : mesurer la fiabilité des machines, planifier la maintenance préventive.
* **IT / Cloud** : mesurer la disponibilité d’un service (ex. serveurs, applications, API).
* **SLA** : souvent exprimé en termes de disponibilité, donc dérivé de MTBF et MTTR.

---

# 📝 Résumé pédagogique

* **MTBF (Mean Time Between Failures)** = fiabilité → “combien de temps ça tourne avant de casser”.
* **MTTR (Mean Time To Repair)** = maintenabilité → “combien de temps pour réparer quand ça casse”.
* Ensemble, ils donnent la **disponibilité** d’un système/machine/service.

---

👉 Veux-tu que je prépare un **schéma visuel type timeline** (fonctionnement → panne → réparation → redémarrage → nouveau cycle), pour illustrer MTBF et MTTR ?
