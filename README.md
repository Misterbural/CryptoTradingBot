
# CryptoBot

Projet basé sur le repo :
`https://github.com/CryptoRobotFr/cBot-Project`

## Installation

Mise en place du projet:  
>git clone https://github.com/Misterbural/CryptoRobot.git

Installation des dépendances:  
>pip install -r requirements.txt  

## Configuration

### Backtesting

Commencez par configurer la liste des paires sur lesquelles vous souhaitez travailler dans pair_list.json (utile pour les stratégies multicoin).

Depuis Vs code ou un autre IDE, téléchargez les données historiques avec les paramètres de votre choix en jouant le notebook Jupyter data_manager.ipynb

Vous pouvez désormais jouer les différents notebook de backtest présents dans le dossier backtest avec vos paramètres.

### Live

Commencez par configurer la liste des paires comme pour le backtest.

Renommez config.json.dist en config.json et renseignez avec vos clés API à destination de FTX.

Une fois que la stratégie est prête, programmez le lancement de la stratégie via crontab en fonction de la timeframe de la stratégie

### Se créer un compte FTX

https://ftx.com/profile#a=11081166

### Améliorations envisagé

Ajouter message Slack proprement

Amélioration backtesting :
- plot_bar_by_month ajout comparaison avec buy and hold (si possible)
- Plot courbe wallet/price logarithmique 
- Plot accumulation cypto

Factoriser code commun strategies/backtests dans utilities (trading conditions, params indicator)