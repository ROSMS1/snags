# 📡 FLM Snags Tracker – MTN Congo

Application mobile/web de gestion des snags terrain, basée sur le modèle du fichier
**FLM_SNAGS_TRACKER_2026_Full_south.xlsx**.

## 🚀 Installation & Lancement

### Prérequis
- Python 3.9+
- pip

### Étapes

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`

## 📱 Fonctionnalités

| Page | Description |
|------|-------------|
| 🏠 **Dashboard** | Vue globale : KPIs, graphiques par région, catégorie, statut |
| ➕ **Nouveau Snag** | Formulaire complet (modèle PM Snags) : site, description, catégorie, plan d'action, matériels |
| 📋 **Liste des Snags** | Tableau filtrable + mise à jour rapide des snags |
| 🔔 **Rappels & Alertes** | Alertes automatiques par couleur : 🔴 En retard / 🟠 ≤7j / 🟡 ≤14j |
| 🔧 **Besoins Matériels** | Suivi spare parts par site (Pending → Ordered → Received → Installed) |
| 🔋 **Plan Batteries** | Suivi du plan de remplacement batteries backup |

## 🗄️ Base de Données

SQLite locale : `snags_tracker.db` (créée automatiquement au 1er lancement)

**Tables :**
- `snags` — Tous les snags (modèle PM Snags)
- `materials` — Besoins en matériels liés aux snags
- `battery_plan` — Plan de remplacement batteries

## 📐 Modèle des données (Snags)

Colonnes identiques à la feuille Excel :
`Number | Site ID | Site Name | Site Priority | Region | PM Auditor | Audit Date |
Snags Description | Category | Sub-Category | Owner | Action Plan | Plan Date |
Deadline | Implementer | Current Progress | Status | Close Date | Comments |
Spare Request | Items | Specifications | Qty | Snag Identification`

## 🔔 Système d'alertes

| Icône | Délai | Action recommandée |
|-------|-------|--------------------|
| 🔴 | En retard (deadline dépassée) | Action immédiate |
| 🔴 | ≤ 3 jours | Urgence critique |
| 🟠 | ≤ 7 jours | Planifier intervention |
| 🟡 | ≤ 14 jours | Préparer l'intervention |
| 🟢 | > 14 jours | Suivi normal |
