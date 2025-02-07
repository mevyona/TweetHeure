import random
import pyfiglet
import os
import platform
import curses
import json

class IDatabase:
    """Interface pour la base de données."""
    
    def createUser(self, username, password):
        """Créer un utilisateur."""
        raise NotImplementedError

    def createPost(self, user, text):
        """Créer un post."""
        raise NotImplementedError

    def getRandomPost(self):
        """Obtenir un post aléatoire."""
        raise NotImplementedError

    def addComment(self, post, user, text):
        """Ajouter un commentaire à un post."""
        raise NotImplementedError

class JsonDatabase(IDatabase):
    """Implémentation de la base de données utilisant un fichier JSON."""
    
    def __init__(self, filename="tweetheure_data.json"):
        self.filename = filename
        self.users = []
        self.posts = []
        self.load_data()

    def save_data(self):
        """Sauvegarder les données dans le fichier JSON."""
        data = {
            "users": [
                {
                    "username": user.username,
                    "password": user.password
                } for user in self.users
            ],
            "posts": [
                {
                    "user": post.user.username,
                    "text": post.text,
                    "comments": [(comment[0].username, comment[1]) for comment in post.comments]
                } for post in self.posts
            ]
        }
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_data(self):
        """Charger les données depuis le fichier JSON."""
        if not os.path.exists(self.filename):
            return

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for user_data in data.get("users", []):
                    self.createUser(user_data["username"], user_data["password"])
                for post_data in data.get("posts", []):
                    user = next((u for u in self.users if u.username == post_data["user"]), None)
                    if user:
                        post = self.createPost(user, post_data["text"])
                        for comment_user, comment_text in post_data["comments"]:
                            commenter = next((u for u in self.users if u.username == comment_user), None)
                            if commenter:
                                post.comment(commenter, comment_text)
        except (json.JSONDecodeError, FileNotFoundError):
            print("Erreur lors du chargement du fichier de données. Démarrage avec une base de données vide.")

    def createUser(self, username, password):
        """Créer un utilisateur et le sauvegarder."""
        user = User(self, username, password)
        self.users.append(user)
        self.save_data()
        return user

    def createPost(self, user, text):
        """Créer un post et le sauvegarder."""
        post = Post(self, user, text)
        self.posts.append(post)
        self.save_data()
        return post

    def getRandomPost(self):
        """Obtenir un post aléatoire."""
        return random.choice(self.posts) if self.posts else None

    def addComment(self, post, user, text):
        """Ajouter un commentaire à un post et le sauvegarder."""
        post.comments.append((user, text))
        self.save_data()

class DatabaseModel:
    """Modèle de base pour les objets de la base de données."""
    
    def __init__(self, database: IDatabase):
        self._database = database

class User(DatabaseModel):
    """Classe représentant un utilisateur."""
    
    def __init__(self, database, username, password):
        super().__init__(database)
        self.username = username
        self.password = password

    def createPost(self, text):
        """Créer un post."""
        return self._database.createPost(self, text)

class Post(DatabaseModel):
    """Classe représentant un post."""
    
    def __init__(self, database, user, text):
        super().__init__(database)
        self.user = user
        self.text = text
        self.comments = []

    def comment(self, user, text):
        """Ajouter un commentaire au post."""
        self._database.addComment(self, user, text)

class App:
    """Classe principale de l'application."""
    
    def __init__(self, database: IDatabase):
        self._database = database
        self.currentUser = None

    def signUp(self, username, password):
        """Inscrire un nouvel utilisateur."""
        if any(u.username == username for u in self._database.users):
            return None
        return self._database.createUser(username, password)

    def logIn(self, username, password):
        """Connecter un utilisateur."""
        for user in self._database.users:
            if user.username == username and user.password == password:
                self.currentUser = user
                return True
        return False

    def logOut(self):
        """Déconnecter l'utilisateur actuel."""
        self.currentUser = None

    def createPost(self, text):
        """Créer un post."""
        if self.currentUser:
            return self.currentUser.createPost(text)
        else:
            print("Vous devez vous connecter d'abord.")
            return None

    def getRandomPost(self):
        """Obtenir un post aléatoire."""
        return self._database.getRandomPost()

class AppCmd(App):
    """Classe pour l'application en mode commande avec interface curses."""
    
    def clearScreen(self):
        """Effacer l'écran."""
        systemName = platform.system()
        if systemName == "Windows":
            os.system('cls')
        else:
            os.system('clear')

    def safe_addstr(self, stdscr, text):
        """Ajouter du texte à l'écran en gérant les erreurs."""
        try:
            stdscr.addstr(text)
            return True
        except curses.error:
            return False

    def displayMenu(self, stdscr):
        """Afficher le menu principal."""
        try:
            asciiArt = pyfiglet.figlet_format("TweetHeure")
            stdscr.clear()
            self.safe_addstr(stdscr, asciiArt)
            self.safe_addstr(stdscr, '\nBienvenue sur TweetHeure!\n')
            if self.currentUser:
                self.safe_addstr(stdscr, f'Vous êtes connecté en tant que : {self.currentUser.username}\n')
            else:
                self.safe_addstr(stdscr, 'Vous n\'êtes pas connecté.\n')
            self.safe_addstr(stdscr, 'Appuyez sur:\n')
            self.safe_addstr(stdscr, '[S] pour S\'inscrire\n')
            self.safe_addstr(stdscr, '[L] pour Se connecter\n')
            self.safe_addstr(stdscr, '[C] pour Créer un post\n')
            self.safe_addstr(stdscr, '[R] pour Voir un post aléatoire\n')
            self.safe_addstr(stdscr, '[M] pour Commenter un post\n')
            self.safe_addstr(stdscr, '[O] pour Se déconnecter\n')
            self.safe_addstr(stdscr, '[E] pour Quitter\n')
            stdscr.refresh()
        except curses.error:
            try:
                stdscr.clear()
                self.safe_addstr(stdscr, "TweetHeure\n")
                self.safe_addstr(stdscr, "S/L/C/R/M/O/E\n")
                stdscr.refresh()
            except curses.error:
                pass

    def handleUserInput(self, stdscr):
        """Gérer les entrées utilisateur."""
        curses.use_default_colors()
        curses.curs_set(1)
        
        while True:
            try:
                self.displayMenu(stdscr)
                key = stdscr.getch()
                if key == ord('s'):
                    self.signUpMenu(stdscr)
                elif key == ord('l'):
                    self.loginMenu(stdscr)
                elif key == ord('c'):
                    self.createPostMenu(stdscr)
                elif key == ord('r'):
                    self.viewRandomPostMenu(stdscr)
                elif key == ord('m'):
                    self.commentMenu(stdscr)
                elif key == ord('o'):
                    self.logOut()
                elif key == ord('e'):
                    break
            except curses.error:
                continue

    def signUpMenu(self, stdscr):
        """Menu pour s'inscrire."""
        try:
            self.clearScreen()
            stdscr.clear()
            self.safe_addstr(stdscr, "Menu d'inscription:\n")
            stdscr.refresh()
            self.safe_addstr(stdscr, 'Entrez le nom d\'utilisateur: ')
            stdscr.refresh()
            curses.echo()
            username = stdscr.getstr().decode('utf-8')
            self.safe_addstr(stdscr, '\nEntrez le mot de passe: ')
            stdscr.refresh()
            password = stdscr.getstr().decode('utf-8')
            curses.noecho()
            user = self.signUp(username, password)
            stdscr.clear()
            if user:
                self.safe_addstr(stdscr, f'Utilisateur {username} inscrit avec succès.\n')
            else:
                self.safe_addstr(stdscr, f'Le nom d\'utilisateur {username} existe déjà.\n')
            stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass

    def loginMenu(self, stdscr):
        """Menu pour se connecter."""
        try:
            self.clearScreen()
            stdscr.clear()
            self.safe_addstr(stdscr, "Menu de connexion:\n")
            stdscr.refresh()
            self.safe_addstr(stdscr, 'Entrez le nom d\'utilisateur: ')
            stdscr.refresh()
            curses.echo()
            username = stdscr.getstr().decode('utf-8')
            self.safe_addstr(stdscr, '\nEntrez le mot de passe: ')
            stdscr.refresh()
            password = stdscr.getstr().decode('utf-8')
            curses.noecho()
            if self.logIn(username, password):
                stdscr.clear()
                self.safe_addstr(stdscr, 'Connecté avec succès.\n')
                stdscr.refresh()
            else:
                stdscr.clear()
                self.safe_addstr(stdscr, 'Nom d\'utilisateur ou mot de passe invalide.\n')
                stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass

    def createPostMenu(self, stdscr):
        """Menu pour créer un post."""
        try:
            if not self.currentUser:
                stdscr.clear()
                self.safe_addstr(stdscr, 'Vous devez vous connecter d\'abord.\n')
                stdscr.refresh()
                stdscr.getch()
                return

            self.clearScreen()
            stdscr.clear()
            self.safe_addstr(stdscr, "Menu de création de post:\n")
            stdscr.refresh()
            self.safe_addstr(stdscr, 'Entrez le texte du post: ')
            stdscr.refresh()
            curses.echo()
            text = stdscr.getstr().decode('utf-8')
            curses.noecho()
            self.createPost(text)
            stdscr.clear()
            self.safe_addstr(stdscr, f'Post créé: {text}\n')
            stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass

    def viewRandomPostMenu(self, stdscr):
        """Menu pour voir un post aléatoire."""
        try:
            self.clearScreen()
            stdscr.clear()
            self.safe_addstr(stdscr, "Menu de visualisation de post aléatoire:\n")
            stdscr.refresh()
            post = self.getRandomPost()
            if post:
                self.safe_addstr(stdscr, f'Post de {post.user.username}: {post.text}\n')
                if post.comments:
                    self.safe_addstr(stdscr, '\nCommentaires:\n')
                    for user, comment in post.comments:
                        self.safe_addstr(stdscr, f'- {user.username}: {comment}\n')
                stdscr.refresh()
            else:
                self.safe_addstr(stdscr, 'Aucun post disponible.\n')
                stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass

    def commentMenu(self, stdscr):
        """Menu pour commenter un post."""
        try:
            if not self.currentUser:
                stdscr.clear()
                self.safe_addstr(stdscr, 'Vous devez vous connecter d\'abord.\n')
                stdscr.refresh()
                stdscr.getch()
                return

            self.clearScreen()
            stdscr.clear()
            self.safe_addstr(stdscr, "Menu de commentaire:\n")
            stdscr.refresh()
            self.safe_addstr(stdscr, 'Entrez le nom d\'utilisateur de la personne dont vous voulez commenter le post: ')
            stdscr.refresh()
            curses.echo()
            username = stdscr.getstr().decode('utf-8')
            curses.noecho()

            userToComment = None
            for user in self._database.users:
                if user.username == username:
                    userToComment = user
                    break

            if not userToComment:
                stdscr.clear()
                self.safe_addstr(stdscr, f'Aucun utilisateur trouvé avec le nom d\'utilisateur: {username}\n')
                stdscr.refresh()
                stdscr.getch()
                return

            stdscr.clear()
            self.safe_addstr(stdscr, f'Posts de {username}:\n')
            stdscr.refresh()

            posts = [post for post in self._database.posts if post.user == userToComment]
            if not posts:
                self.safe_addstr(stdscr, 'Aucun post disponible de cet utilisateur.\n')
                stdscr.refresh()
                stdscr.getch()
                return

            for idx, post in enumerate(posts):
                self.safe_addstr(stdscr, f'{idx + 1}. {post.text}\n')
            stdscr.refresh()

            self.safe_addstr(stdscr, 'Entrez le numéro du post à commenter: ')
            stdscr.refresh()
            curses.echo()
            postChoice = stdscr.getstr().decode('utf-8')
            curses.noecho()

            try:
                postChoice = int(postChoice)
                if 1 <= postChoice <= len(posts):
                    postToComment = posts[postChoice - 1]
                else:
                    raise ValueError
            except ValueError:
                stdscr.clear()
                self.safe_addstr(stdscr, 'Choix invalide. Veuillez sélectionner un numéro de post valide.\n')
                stdscr.refresh()
                stdscr.getch()
                return

            stdscr.clear()
            self.safe_addstr(stdscr, f'Entrez votre commentaire pour le post: "{postToComment.text}"\n')
            stdscr.refresh()
            curses.echo()
            commentText = stdscr.getstr().decode('utf-8')
            curses.noecho()

            postToComment.comment(self.currentUser, commentText)
            stdscr.clear()
            self.safe_addstr(stdscr, f'Commentaire ajouté au post: {postToComment.text}\n')
            stdscr.refresh()
            stdscr.getch()
        except curses.error:
            pass

def main(stdscr):
    """Fonction principale pour démarrer l'application."""
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    stdscr.keypad(1)
    db = JsonDatabase()
    app = AppCmd(db)
    app.handleUserInput(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
