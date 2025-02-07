import sqlite3
import curses
import pyfiglet

conn = sqlite3.connect("tweetheure.db")
cursor = conn.cursor()

cursor.executescript("""
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
conn.commit()

currentUser = None

def safeAddStr(stdscr, text):
    try:
        stdscr.addstr(text)
    except curses.error:
        pass

def getInput(stdscr, prompt):
    stdscr.clear()
    safeAddStr(stdscr, prompt)
    stdscr.refresh()
    inputText = ""
    
    while True:
        key = stdscr.getch()
        
        if key == 10:
            break
        elif key == 27:
            inputText = ""
            break
        elif key == 263:
            inputText = inputText[:-1]
        elif 32 <= key <= 126:
            inputText += chr(key)
        
        stdscr.clear()
        safeAddStr(stdscr, prompt + inputText)
        stdscr.refresh()
    
    return inputText

def displayMessage(stdscr, message, delay=2000):
    stdscr.clear()
    safeAddStr(stdscr, message)
    stdscr.refresh()
    curses.napms(delay)

def displayMenu(stdscr):
    global currentUser
    try:
        asciiArt = pyfiglet.figlet_format("TweetHeure")
        stdscr.clear()
        safeAddStr(stdscr, asciiArt)
        safeAddStr(stdscr, '\nBienvenue sur TweetHeure !\n')

        if currentUser:
            safeAddStr(stdscr, f'Vous êtes connecté en tant que : {currentUser[1]}\n')
        else:
            safeAddStr(stdscr, 'Vous n\'êtes pas connecté.\n')

        safeAddStr(stdscr, 'Appuyez sur:\n')
        safeAddStr(stdscr, '[C] pour Créer un compte\n')
        safeAddStr(stdscr, '[L] pour Se connecter\n')
        safeAddStr(stdscr, '[O] pour Se déconnecter\n')
        safeAddStr(stdscr, '[P] pour Publier un post\n')
        safeAddStr(stdscr, '[V] pour Voir les posts\n')
        safeAddStr(stdscr, '[M] pour Commenter un post\n')
        safeAddStr(stdscr, '[Q] pour Quitter\n')

        stdscr.refresh()
    except curses.error:
        pass

def createAccount(stdscr):
    global currentUser
    stdscr.clear()
    name = getInput(stdscr, "Entrez votre nom : ")
    email = getInput(stdscr, "Entrez votre email : ")
    password = getInput(stdscr, "Entrez votre mot de passe : ")

    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        displayMessage(stdscr, "✅ Compte créé avec succès !")
    except sqlite3.IntegrityError:
        displayMessage(stdscr, "❌ Erreur : Cet email est déjà utilisé.")
    stdscr.refresh()
    stdscr.getch()

def login(stdscr):
    global currentUser
    stdscr.clear()
    email = getInput(stdscr, "Entrez votre email : ")
    password = getInput(stdscr, "Entrez votre mot de passe : ")

    cursor.execute("SELECT id, name FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()

    if user:
        currentUser = user
        displayMessage(stdscr, f"✅ Connecté en tant que {user[1]}")
    else:
        displayMessage(stdscr, "❌ Identifiants incorrects.")
    stdscr.refresh()
    stdscr.getch()

def logout(stdscr):
    global currentUser
    if currentUser:
        displayMessage(stdscr, f"👋 Au revoir {currentUser[1]} !")
        currentUser = None
    else:
        displayMessage(stdscr, "⚠️ Vous n'êtes pas connecté.")
    stdscr.refresh()
    stdscr.getch()

def addPost(stdscr):
    global currentUser
    stdscr.clear()
    if not currentUser:
        displayMessage(stdscr, "❌ Vous devez être connecté pour publier un post.")
        return

    title = getInput(stdscr, "Titre du post : ")
    content = getInput(stdscr, "Contenu du post : ")

    cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)", (currentUser[0], title, content))
    conn.commit()
    displayMessage(stdscr, "✅ Post ajouté avec succès.")

def viewPosts(stdscr):
    stdscr.clear()
    cursor.execute("SELECT posts.id, users.name, posts.title, posts.content FROM posts JOIN users ON posts.user_id = users.id")
    posts = cursor.fetchall()

    if not posts:
        displayMessage(stdscr, "⚠️ Aucun post disponible.")
        return

    for post in posts:
        safeAddStr(stdscr, f"\n📌 {post[2]} (par {post[1]})\n")
        safeAddStr(stdscr, f"   {post[3]}\n")
        safeAddStr(stdscr, f"   [ID du post : {post[0]}]\n")
        
        cursor.execute("""
            SELECT users.name, comments.content 
            FROM comments 
            JOIN users ON comments.user_id = users.id 
            WHERE comments.post_id = ?
        """, (post[0],))
        comments = cursor.fetchall()
        
        if comments:
            safeAddStr(stdscr, "   Commentaires :\n")
            for comment in comments:
                safeAddStr(stdscr, f"   - {comment[0]} : {comment[1]}\n")
        else:
            safeAddStr(stdscr, "   Aucun commentaire\n")
    
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)

def addComment(stdscr):
    global currentUser
    stdscr.clear()
    if not currentUser:
        displayMessage(stdscr, "❌ Vous devez être connecté pour commenter.")
        return

    cursor.execute("""
        SELECT posts.id, users.name, posts.title, posts.content 
        FROM posts 
        JOIN users ON posts.user_id = users.id
    """)
    posts = cursor.fetchall()

    if not posts:
        displayMessage(stdscr, "⚠️ Aucun post disponible.")
        return

    viewPosts(stdscr)
    
    stdscr.refresh()
    stdscr.nodelay(False)
    
    postId = getInput(stdscr, "ID du post à commenter : ")

    cursor.execute("SELECT id FROM posts WHERE id = ?", (postId,))
    if not cursor.fetchone():
        displayMessage(stdscr, "⚠️ Ce post n'existe pas.")
        return

    content = getInput(stdscr, "Votre commentaire : ")
    
    cursor.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)", (postId, currentUser[0], content))
    conn.commit()
    displayMessage(stdscr, "✅ Commentaire ajouté.")
    
    stdscr.getch()
    stdscr.nodelay(True)

def main(stdscr):
    global currentUser
    curses.curs_set(0)
    stdscr.timeout(100)
    
    while True:
        try:
            displayMenu(stdscr)
            key = stdscr.getch()

            if key == ord('C') or key == ord('c'):
                createAccount(stdscr)
            elif key == ord('L') or key == ord('l'):
                login(stdscr)
            elif key == ord('O') or key == ord('o'):
                logout(stdscr)
            elif key == ord('P') or key == ord('p'):
                addPost(stdscr)
            elif key == ord('V') or key == ord('v'):
                viewPosts(stdscr)
            elif key == ord('M') or key == ord('m'):
                addComment(stdscr)
            elif key == ord('Q') or key == ord('q'):
                break
        except curses.error:
            continue

if __name__ == "__main__":
    curses.wrapper(main)

conn.close()