# ✅ Corrigés enrichis – Exploitation des données

---

## 🛒 **Scénario 1 – ShopNow (recommandations e-commerce)**

**Sources possibles** :

* Journaux de navigation web (clics, pages vues, recherches) → récupérés via le site.
* Historique d’achats → base de données interne.
* Catalogue produit → base interne avec infos produits.

**Traitements / Analyses** :

* Nettoyer les clics (retirer robots, doublons).
* Regrouper les produits consultés et achetés par utilisateur.
* Faire des **statistiques d’association** : “les clients qui ont vu ce produit achètent souvent aussi celui-là”.
* Croiser navigation + achats pour identifier les préférences (par ex. un client regarde souvent des baskets mais n’achète pas → suggestion ciblée).

**Utilisation** :

* Générer une liste de recommandations sur le site.
* Aider le marketing à créer des campagnes ciblées (“clients intéressés par sport mais n’ont pas acheté”).

---

## 💳 **Scénario 2 – EuroSecure (fraude bancaire)**

**Sources possibles** :

* Transactions bancaires en temps réel (flux interne).
* Données clients (profil, pays, habitudes) → base interne.
* Listes externes (cartes volées, comptes suspects) → API de sécurité.

**Traitements / Analyses** :

* Croiser chaque transaction avec le **profil client** (ex. Sophie dépense habituellement < 200 €, et là 1200 € → suspect).
* Vérifier la **cohérence géographique** (achat à Singapour + téléphone géolocalisé à Paris).
* Comparer avec des **listes noires**.
* Faire des **statistiques de fréquence** (trop d’achats en peu de temps).

**Utilisation** :

* Déclencher une **alerte automatique** pour les analystes.
* Bloquer temporairement une carte si le risque est élevé.
* Réduire les pertes financières de la banque.

---

## 🏭 **Scénario 3 – AutoMec (maintenance prédictive)**

**Sources possibles** :

* Capteurs IoT (température, vibrations, énergie).
* Logs machines (fichiers internes).
* Historique des maintenances → base interne.

**Traitements / Analyses** :

* Suivre les **tendances des capteurs** (température qui monte régulièrement).
* Faire des **agrégations** (moyennes par heure, pics de vibration).
* Comparer avec l’**historique de pannes** pour voir si les mêmes schémas reviennent.
* Détecter les **valeurs anormales** (une machine chauffe plus que les autres).

**Utilisation** :

* Générer une **alerte préventive** avant qu’une panne survienne.
* Planifier la maintenance au bon moment (éviter l’arrêt de production).

---

## ✈️ **Scénario 4 – SkyAir (bad buzz réseaux sociaux)**

**Sources possibles** :

* Messages réseaux sociaux (API Twitter, Facebook).
* Réclamations clients (CRM interne).
* Articles de presse (sites d’actualités, scraping).

**Traitements / Analyses** :

* Nettoyer les données (enlever doublons, spam).
* Compter le **nombre de messages positifs/négatifs** (analyse de sentiment).
* Croiser avec les réclamations clients (beaucoup de tweets + hausse des réclamations = alerte forte).
* Identifier les **thèmes récurrents** (retards, bagages perdus…).

**Utilisation** :

* Créer un **tableau de bord en temps réel** de l’image de la marque.
* Détecter rapidement un **bad buzz** et réagir avant qu’il devienne viral.

---

## 🏥 **Scénario 5 – CarePlus (fraude santé)**

**Sources possibles** :

* Factures médicales (fichiers XML/CSV des praticiens).
* Dossiers patients (données semi-structurées internes).
* Historique de remboursements (base SQL interne).

**Traitements / Analyses** :

* Standardiser les données (codes des actes médicaux).
* Anonymiser les données personnelles (RGPD).
* Croiser les **factures et historiques** pour trouver des incohérences (ex : patient facturé alors qu’il est en vacances).
* Faire des **statistiques comparatives** : un médecin facture beaucoup plus que la moyenne → suspect.

**Utilisation** :

* Repérer les fraudes et limiter les remboursements abusifs.
* Générer des **rapports d’anomalies** pour les analystes internes.

---

## 🏙️ **Scénario 6 – NeoCity (mobilité urbaine)**

**Sources possibles** :

* GPS bus/trams (API opérateurs transport).
* Capteurs routiers (flux de véhicules).
* Données météo (API externe).
* Occupation parkings (open data).
* Événements (matchs, concerts).

**Traitements / Analyses** :

* Croiser **données transports + météo** (pluie = trajets bus plus longs).
* Faire des **statistiques horaires** (heures de pointe, embouteillages).
* Prévoir les **pics de trafic** avec météo + événements.
* Identifier les zones où le trafic est le plus saturé.

**Utilisation** :

* Fournir une **application citoyenne** (temps d’attente bus, trafic).
* Aider la mairie à optimiser les trajets et horaires.

---

## ⚡ **Scénario 7 – GreenWatt (prévision énergétique)**

**Sources possibles** :

* Mesures des compteurs intelligents (IoT).
* Historique de factures clients (BDD interne).
* Données météo (API météo).
* Calendrier (jours fériés, vacances).

**Traitements / Analyses** :

* Agréger la consommation par heure/jour.
* Identifier les **pics de consommation** (ex. pendant la canicule).
* Croiser consommation + météo pour **expliquer les pics**.
* Faire des **prévisions simples** : estimer la consommation demain en fonction de la météo prévue.

**Utilisation** :

* Anticiper les **pics de demande** pour éviter les coupures.
* Adapter les tarifs selon les périodes de forte consommation.

---

⚡ **Résultat pédagogique** :
Les apprenants débutants apprennent à :

1. **Chercher où trouver les données** (BDD, API, capteurs, fichiers).
2. **Proposer un traitement concret** (statistiques, croisement, détection d’anomalies, agrégation, prévision).
3. **Relier à une utilisation métier** (alerte, tableau de bord, recommandation, optimisation).

---

👉 Veux-tu que je mette tout ça dans un **document imprimable (fiches exercices + corrigés)** ou dans un **support de diapo interactif** pour animer la formation ?
