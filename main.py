import sqlite3
import curses
import pyfiglet
import curses.ascii
import re
import os
import bcrypt
import json

class TweetHeureApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.currentUser = None
        self.conn = None
        self.cursor = None
        curses.curs_set(0)
        self.stdscr.keypad(True)

        if not self.loadSession():
            self.storage_mode = self.getStorageMode()
            if self.storage_mode == 'sql':
                self.initSQL()
            else:
                self.initJSON()

    def getStorageMode(self):
        asciiArt = pyfiglet.figlet_format("TweetHeure")
        self.stdscr.clear()
        self.safeAddStr(asciiArt)
        self.safeAddStr("Choisissez le mode de stockage :\n")
        self.safeAddStr("[S] pour SQL\n")
        self.safeAddStr("[J] pour JSON\n")
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key in [ord('S'), ord('s')]:
                return 'sql'
            elif key in [ord('J'), ord('j')]:
                return 'json'

    def initSQL(self):
        self.conn = sqlite3.connect("tweetheure.db")
        self.cursor = self.conn.cursor()
        self.createTables()

    def initJSON(self):
        if not os.path.exists('data.json'):
            with open('data.json', 'w') as f:
                json.dump({'users': [], 'posts': [], 'comments': []}, f)

    def createTables(self):
        self.cursor.executescript(""" 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            content TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        self.conn.commit()

    def loadSession(self):
        session_file = '.session'
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            user_id = session_data.get('user_id')
            storage_mode = session_data.get('storage_mode')
            if user_id and storage_mode:
                self.storage_mode = storage_mode
                if self.storage_mode == 'sql':
                    self.initSQL()
                    self.cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
                    user = self.cursor.fetchone()
                else:
                    self.initJSON()
                    with open('data.json', 'r') as f:
                        data = json.load(f)
                    user = next((u for u in data['users'] if u['id'] == int(user_id)), None)
                if user:
                    self.currentUser = user
                    return True
        return False

    def saveSession(self, user_id):
        session_data = {
            'user_id': user_id,
            'storage_mode': self.storage_mode
        }
        with open('.session', 'w') as f:
            json.dump(session_data, f)

    def safeAddStr(self, text):
        try:
            self.stdscr.addstr(text)
        except curses.error:
            pass

    def getInput(self, prompt):
        self.stdscr.clear()
        self.safeAddStr(prompt)
        self.stdscr.refresh()
        inputText = ""

        while True:
            key = self.stdscr.getch()
            if key == 10:
                break
            elif key == 27:
                inputText = ""
                break
            elif key in (curses.KEY_BACKSPACE, 127, 8) and len(inputText) > 0:
                inputText = inputText[:-1]
            elif curses.ascii.isprint(key) or (128 <= key <= 255):
                inputText += chr(key)
            self.stdscr.clear()
            self.safeAddStr(prompt + inputText)
            self.stdscr.refresh()

        return inputText

    def displayMessage(self, message, delay=2000):
        self.stdscr.clear()
        self.safeAddStr(message)
        self.stdscr.refresh()
        curses.napms(delay)

    def displayMenu(self):
        try:
            asciiArt = pyfiglet.figlet_format("TweetHeure")
            self.stdscr.clear()
            self.safeAddStr(asciiArt)
            self.safeAddStr('\nBienvenue sur TweetHeure !\n')
            if self.currentUser:
                if isinstance(self.currentUser, dict):
                    self.safeAddStr(f'Vous êtes connecté(e) en tant que : {self.currentUser["name"]}\n')
                else:
                    self.safeAddStr(f'Vous êtes connecté(e) en tant que : {self.currentUser[1]}\n')
            else:
                self.safeAddStr('Vous n\'êtes pas connecté(e).\n')
            self.safeAddStr('Appuyez sur:\n')
            self.safeAddStr('[C] pour Créer un compte\n')
            self.safeAddStr('[L] pour Se connecter\n')
            self.safeAddStr('[O] pour Se déconnecter\n')
            self.safeAddStr('[P] pour Publier un post\n')
            self.safeAddStr('[V] pour Voir les posts\n')
            self.safeAddStr('[M] pour Commenter un post\n')
            self.safeAddStr('[Z] pour Modifier la méthode de stockage\n')
            self.safeAddStr('[Q] pour Quitter\n')
            self.stdscr.refresh()
        except curses.error:
            pass

    def run(self):
        while True:
            try:
                self.displayMenu()
                key = self.stdscr.getch()
                if key in [ord('C'), ord('c')]:
                    UserManagement(self).createAccount()
                elif key in [ord('L'), ord('l')]:
                    UserManagement(self).login()
                elif key in [ord('O'), ord('o')]:
                    UserManagement(self).logout()
                elif key in [ord('P'), ord('p')]:
                    PostManagement(self).addPost()
                elif key in [ord('V'), ord('v')]:
                    PostManagement(self).viewPosts()
                elif key in [ord('M'), ord('m')]:
                    CommentManagement(self).addComment()
                elif key in [ord('Z'), ord('z')]:
                    self.changeStorageMode()
                elif key in [ord('Q'), ord('q')]:
                    break
            except curses.error:
                continue
        os.system('cls' if os.name == 'nt' else 'clear')

    def changeStorageMode(self):
        self.displayMessage("Vous allez être déconnecté(e). Appuyez sur [O] pour continuer, [N] pour annuler.")
        key = self.stdscr.getch()
        if key in [ord('o'), ord('O')]:
            if os.path.exists('.session'):
                os.remove('.session')
            curses.endwin()
            curses.wrapper(main)
        else:
            self.displayMessage("Opération annulée.")
            self.stdscr.refresh()
            self.stdscr.getch()

class UserManagement:
    def __init__(self, app):
        self.app = app

    def isValidEmail(self, email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) and not re.search(r'[À-ÿ]', email)

    def hashPassword(self, password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt)

    def verifyPassword(self, password, hashedPassword):
        return bcrypt.checkpw(password.encode(), hashedPassword)

    def createAccount(self):
        self.app.stdscr.clear()
        name = self.app.getInput("Entrez votre nom : ")
        email = self.app.getInput("Entrez votre email : ")
        if not self.isValidEmail(email):
            self.app.displayMessage("❌ Erreur : Email invalide")
            return self.createAccount()
        password = self.app.getInput("Entrez votre mot de passe : ")
        hashedPassword = self.hashPassword(password)

        if self.app.storage_mode == 'sql':
            try:
                self.app.cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, hashedPassword)
                )
                self.app.conn.commit()
                self.app.displayMessage("✅ Compte créé avec succès !")
            except sqlite3.IntegrityError:
                self.app.displayMessage("❌ Erreur : Utilisateur déjà existant.")
        else:
            with open('data.json', 'r+') as f:
                data = json.load(f)
                if any(user['email'] == email for user in data['users']):
                    self.app.displayMessage("❌ Erreur : Utilisateur déjà existant.")
                else:
                    user_id = len(data['users']) + 1
                    data['users'].append({
                        'id': user_id,
                        'name': name,
                        'email': email,
                        'password': hashedPassword.decode()
                    })
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    self.app.displayMessage("✅ Compte créé avec succès !")
        self.app.stdscr.refresh()
        self.app.stdscr.getch()

    def login(self):
        self.app.stdscr.clear()
        email = self.app.getInput("Entrez votre email : ")
        password = self.app.getInput("Entrez votre mot de passe : ")

        if self.app.storage_mode == 'sql':
            self.app.cursor.execute("SELECT id, name, password FROM users WHERE email = ?", (email,))
            user = self.app.cursor.fetchone()
        else:
            with open('data.json', 'r') as f:
                data = json.load(f)
            user = next((u for u in data['users'] if u['email'] == email), None)

        if user:
            if self.app.storage_mode == 'sql':
                stored_pw = user[2]
                if self.verifyPassword(password, stored_pw):
                    self.app.currentUser = (user[0], user[1])
                    self.app.saveSession(user[0])
                    self.app.displayMessage(f"✅ Connecté(e) en tant que {user[1]}")
                else:
                    self.app.displayMessage("❌ Identifiants incorrects.")
            else:
                stored_pw = user['password']
                if self.verifyPassword(password, stored_pw.encode()):
                    self.app.currentUser = (user['id'], user['name'])
                    self.app.saveSession(user['id'])
                    self.app.displayMessage(f"✅ Connecté(e) en tant que {user['name']}")
                else:
                    self.app.displayMessage("❌ Identifiants incorrects.")
        else:
            self.app.displayMessage("❌ Identifiants incorrects.")

        self.app.stdscr.refresh()
        self.app.stdscr.getch()

    def logout(self):
        if self.app.currentUser:
            if isinstance(self.app.currentUser, dict):
                self.app.displayMessage(f"👋 Au revoir {self.app.currentUser['name']} !")
            else:
                self.app.displayMessage(f"👋 Au revoir {self.app.currentUser[1]} !")
            self.app.currentUser = None
            if os.path.exists('.session'):
                os.remove('.session')
        else:
            self.app.displayMessage("⚠️ Vous n'êtes pas connecté(e).")
        self.app.stdscr.refresh()
        self.app.stdscr.getch()

class PostManagement:
    def __init__(self, app):
        self.app = app

    def addPost(self):
        self.app.stdscr.clear()
        if not self.app.currentUser:
            self.app.displayMessage("❌ Vous devez être connecté(e) pour publier un post.")
            return
        title = self.app.getInput("Titre du post : ")
        content = self.app.getInput("Contenu du post : ")

        if self.app.storage_mode == 'sql':
            self.app.cursor.execute(
                "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                (self.app.currentUser[0], title, content)
            )
            self.app.conn.commit()
        else:
            with open('data.json', 'r+') as f:
                data = json.load(f)
            post_id = len(data['posts']) + 1
            data['posts'].append({
                'id': post_id,
                'user_id': self.app.currentUser[0],
                'title': title,
                'content': content
            })
            with open('data.json', 'w') as f:
                json.dump(data, f, indent=4)

        self.app.displayMessage("✅ Post ajouté avec succès.")

    def viewPosts(self):
        self.app.stdscr.clear()
        if self.app.storage_mode == 'sql':
            self.app.cursor.execute(
                "SELECT posts.id, users.name, posts.title, posts.content "
                "FROM posts JOIN users ON posts.user_id = users.id"
            )
            posts = self.app.cursor.fetchall()
        else:
            with open('data.json', 'r') as f:
                data = json.load(f)
            posts = [
                (post['id'],
                next(u['name'] for u in data['users'] if u['id'] == post['user_id']),
                post['title'],
                post['content'])
                for post in data['posts']
            ]

        if not posts:
            self.app.displayMessage("⚠️ Aucun post disponible.")
            return

        for p in posts:
            self.app.safeAddStr(f"\n📌 {p[2]} (par {p[1]})\n")
            self.app.safeAddStr(f"   {p[3]}\n")
            self.app.safeAddStr(f"   [ID du post : {p[0]}]\n")
            if self.app.storage_mode == 'sql':
                self.app.cursor.execute(
                    "SELECT users.name, comments.content "
                    "FROM comments JOIN users ON comments.user_id = users.id "
                    "WHERE comments.post_id = ?", (p[0],)
                )
                comments = self.app.cursor.fetchall()
            else:
                with open('data.json', 'r') as f:
                    data = json.load(f)
                comments = [
                    (next(u['name'] for u in data['users'] if u['id'] == c['user_id']), c['content'])
                    for c in data['comments'] if c['post_id'] == p[0]
                ]
            if comments:
                self.app.safeAddStr("   Commentaires :\n")
                for c in comments:
                    self.app.safeAddStr(f"   - {c[0]} : {c[1]}\n")
            else:
                self.app.safeAddStr("   Aucun commentaire\n")
        self.app.stdscr.refresh()
        self.app.stdscr.getch()

class CommentManagement:
    def __init__(self, app):
        self.app = app

    def addComment(self):
        self.app.stdscr.clear()
        if not self.app.currentUser:
            self.app.displayMessage("❌ Vous devez être connecté(e) pour commenter.")
            return

        if self.app.storage_mode == 'sql':
            self.app.cursor.execute(
                "SELECT posts.id, users.name, posts.title, posts.content "
                "FROM posts JOIN users ON posts.user_id = users.id"
            )
            posts = self.app.cursor.fetchall()
        else:
            with open('data.json', 'r') as f:
                data = json.load(f)
            posts = [
                (post['id'],
                 next(u['name'] for u in data['users'] if u['id'] == post['user_id']),
                 post['title'],
                 post['content'])
                for post in data['posts']
            ]

        if not posts:
            self.app.displayMessage("⚠️ Aucun post disponible.")
            return

        PostManagement(self.app).viewPosts()
        self.app.stdscr.refresh()
        self.app.stdscr.nodelay(False)

        postId = self.app.getInput("ID du post à commenter : ")
        if self.app.storage_mode == 'sql':
            self.app.cursor.execute("SELECT id FROM posts WHERE id = ?", (postId,))
            if not self.app.cursor.fetchone():
                self.app.displayMessage("⚠️ Ce post n'existe pas.")
                return
        else:
            with open('data.json', 'r') as f:
                data = json.load(f)
            if not any(int(postId) == p['id'] for p in data['posts']):
                self.app.displayMessage("⚠️ Ce post n'existe pas.")
                return

        content = self.app.getInput("Votre commentaire : ")
        if self.app.storage_mode == 'sql':
            self.app.cursor.execute(
                "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
                (postId, self.app.currentUser[0], content)
            )
            self.app.conn.commit()
        else:
            with open('data.json', 'r+') as f:
                data = json.load(f)
            comment_id = len(data['comments']) + 1
            data['comments'].append({
                'id': comment_id,
                'post_id': int(postId),
                'user_id': self.app.currentUser[0],
                'content': content
            })
            with open('data.json', 'w') as f:
                json.dump(data, f, indent=4)
        self.app.displayMessage("✅ Commentaire ajouté.")

        self.app.stdscr.getch()
        self.app.stdscr.nodelay(True)

def main(stdscr):
    app = TweetHeureApp(stdscr)
    app.run()

if __name__ == "__main__":
    curses.wrapper(main)