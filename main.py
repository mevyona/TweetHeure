import subprocess

choice = input("Quelle version de stockage de données voulez-vous utiliser ? (SQL/JSON) ").upper()

match choice:
    case "SQL":
        subprocess.run(["python", "./dataMethods/TweetHeureSQL.py"])
    case "JSON":
        subprocess.run(["python", "./dataMethods/TweetHeureJSON.py"])
    case _:
        print("Choix invalide. Veuillez entrer 'SQL' ou 'JSON'.")