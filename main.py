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
        self.storage_mode = self.getStorageMode()
        self.currentUser = None
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.loadSession()
        
    def getStorageMode(self):
        self.stdscr.clear()
        self.safeAddStr("Choisissez le mode de stockage :\n")
        self.safeAddStr("[S] pour SQL\n")
        self.safeAddStr("[J] pour JSON\n")
        self.stdscr.refresh()
        while True:
            key = self.stdscr.getch()
            if key == ord('S') or key == ord('s'):
                self.initSQL()
                return 'sql'
            elif key == ord('J') or key == ord('j'):
                self.initJSON()
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
            password TEXT NOT NULL
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
                user_id = f.read().strip()
                if user_id:
                    if self.storage_mode == 'sql':
                        self.cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
                        user = self.cursor.fetchone()
                    else:
                        with open('data.json', 'r') as f:
                            data = json.load(f)
                            user = next((u for u in data['users'] if u['id'] == int(user_id)), None)
                    if user:
                        self.currentUser = user

    def saveSession(self, user_id):
        with open('.session', 'w') as f:
            f.write(str(user_id))

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
                self.safeAddStr(f'Vous êtes connecté en tant que : {self.currentUser[1]}\n')
            else:
                self.safeAddStr('Vous n\'êtes pas connecté.\n')

            self.safeAddStr('Appuyez sur:\n')
            self.safeAddStr('[C] pour Créer un compte\n')
            self.safeAddStr('[L] pour Se connecter\n')
            self.safeAddStr('[O] pour Se déconnecter\n')
            self.safeAddStr('[P] pour Publier un post\n')
            self.safeAddStr('[V] pour Voir les posts\n')
            self.safeAddStr('[M] pour Commenter un post\n')
            self.safeAddStr('[Q] pour Quitter\n')

            self.stdscr.refresh()
        except curses.error:
            pass

    def run(self):
        while True:
            try:
                self.displayMenu()
                key = self.stdscr.getch()

                if key == ord('C') or key == ord('c'):
                    UserManagement(self).createAccount()
                elif key == ord('L') or key == ord('l'):
                    UserManagement(self).login()
                elif key == ord('O') or key == ord('o'):
                    UserManagement(self).logout()
                elif key == ord('P') or key == ord('p'):
                    PostManagement(self).addPost()
                elif key == ord('V') or key == ord('v'):
                    PostManagement(self).viewPosts()
                elif key == ord('M') or key == ord('m'):
                    CommentManagement(self).addComment()
                elif key == ord('Q') or key == ord('q'):
                    break
            except curses.error:
                continue

class UserManagement:
    def __init__(self, app):
        self.app = app

    def isValidEmail(self, email):
        emailPattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(emailPattern, email) and not re.search(r'[À-ÿ]', email)

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
                self.app.cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", 
                                        (name, email, hashedPassword))
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
                    data['users'].append({'id': user_id, 'name': name, 'email': email, 'password': hashedPassword.decode()})
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

        if user and self.verifyPassword(password, user['password'].encode() if self.app.storage_mode == 'json' else user[2]):
            self.app.currentUser = (user['id'], user['name'])
            self.app.saveSession(user['id'] if self.app.storage_mode == 'json' else user[0])
            self.app.displayMessage(f"✅ Connecté en tant que {user['name'] if self.app.storage_mode == 'json' else user[1]}")
        else:
            self.app.displayMessage("❌ Identifiants incorrects.")
        self.app.stdscr.refresh()
        self.app.stdscr.getch()

    def logout(self):
        if self.app.currentUser:
            self.app.displayMessage(f"👋 Au revoir {self.app.currentUser[1]} !")
            self.app.currentUser = None
            os.remove('.session')
        else:
            self.app.displayMessage("⚠️ Vous n'êtes pas connecté.")
        self.app.stdscr.refresh()
        self.app.stdscr.getch()

class PostManagement:
    def __init__(self, app):
        self.app = app

    def addPost(self):
        self.app.stdscr.clear()
        if not self.app.currentUser:
            self.app.displayMessage("❌ Vous devez être connecté pour publier un post.")
            return

        title = self.app.getInput("Titre du post : ")
        content = self.app.getInput("Contenu du post : ")

        if self.app.storage_mode == 'sql':
            self.app.cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)", (self.app.currentUser[0], title, content))
            self.app.conn.commit()
        else:
            with open('data.json', 'r+') as f:
                data = json.load(f)
                post_id = len(data['posts']) + 1
                data['posts'].append({'id': post_id, 'user_id': self.app.currentUser[0], 'title': title, 'content': content})
                f.seek(0)
                json.dump(data, f, indent=4)
        self.app.displayMessage("✅ Post ajouté avec succès.")

    def viewPosts(self):
        self.app.stdscr.clear()
        if self.app.storage_mode == 'sql':
            self.app.cursor.execute("SELECT posts.id, users.name, posts.title, posts.content FROM posts JOIN users ON posts.user_id = users.id")
            posts = self.app.cursor.fetchall()
        else:
            with open('data.json', 'r') as f:
                data = json.load(f)
                posts = [(post['id'], next(user['name'] for user in data['users'] if user['id'] == post['user_id']), post['title'], post['content']) for post in data['posts']]

        if not posts:
            self.app.displayMessage("⚠️ Aucun post disponible.")
            return

        for post in posts:
            self.app.safeAddStr(f"\n📌 {post[2]} (par {post[1]})\n")
            self.app.safeAddStr(f"   {post[3]}\n")
            self.app.safeAddStr(f"   [ID du post : {post[0]}]\n")
            
            if self.app.storage_mode == 'sql':
                self.app.cursor.execute("""
                    SELECT users.name, comments.content 
                    FROM comments 
                    JOIN users ON comments.user_id = users.id 
                    WHERE comments.post_id = ?
                """, (post[0],))
                comments = self.app.cursor.fetchall()
            else:
                with open('data.json', 'r') as f:
                    data = json.load(f)
                    comments = [(next(user['name'] for user in data['users'] if user['id'] == comment['user_id']), comment['content']) for comment in data['comments'] if comment['post_id'] == post[0]]
            
            if comments:
                self.app.safeAddStr("   Commentaires :\n")
                for comment in comments:
                    self.app.safeAddStr(f"   - {comment[0]} : {comment[1]}\n")
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
            self.app.displayMessage("❌ Vous devez être connecté pour commenter.")
            return

        if self.app.storage_mode == 'sql':
            self.app.cursor.execute("""
                SELECT posts.id, users.name, posts.title, posts.content 
                FROM posts 
                JOIN users ON posts.user_id = users.id
            """)
            posts = self.app.cursor.fetchall()
        else:
            with open('data.json', 'r') as f:
                data = json.load(f)
                posts = [(post['id'], next(user['name'] for user in data['users'] if user['id'] == post['user_id']), post['title'], post['content']) for post in data['posts']]

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
                if not any(post['id'] == int(postId) for post in data['posts']):
                    self.app.displayMessage("⚠️ Ce post n'existe pas.")
                    return

        content = self.app.getInput("Votre commentaire : ")
        
        if self.app.storage_mode == 'sql':
            self.app.cursor.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)", (postId, self.app.currentUser[0], content))
            self.app.conn.commit()
        else:
            with open('data.json', 'r+') as f:
                data = json.load(f)
                comment_id = len(data['comments']) + 1
                data['comments'].append({'id': comment_id, 'post_id': int(postId), 'user_id': self.app.currentUser[0], 'content': content})
                f.seek(0)
                json.dump(data, f, indent=4)
        self.app.displayMessage("✅ Commentaire ajouté.")
        
        self.app.stdscr.getch()
        self.app.stdscr.nodelay(True)

def main(stdscr):
    app = TweetHeureApp(stdscr)
    app.run()

if __name__ == "__main__":
    curses.wrapper(main)