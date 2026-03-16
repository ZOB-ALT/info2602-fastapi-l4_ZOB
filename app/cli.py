import typer
import csv
from tabulate import tabulate
from sqlmodel import select
from .database import create_db_and_tables, get_cli_session, drop_all
from .models import RegularUser, Todo, Category, TodoCategory
from .auth import encrypt_password

cli = typer.Typer()

@cli.command()
def initialize():
    with get_cli_session() as db:
        drop_all()
        create_db_and_tables()
        bob = RegularUser(username='bob', email='bob@mail.com', password=encrypt_password('bobpass'))
        rick = RegularUser(username='rick', email='rick@mail.com', password=encrypt_password('rickpass'))
        sally = RegularUser(username='sally', email='sally@mail.com', password=encrypt_password('sallypass'))
        db.add_all([bob, rick, sally])
        db.commit()

        with open('todos.csv') as file:
            reader = csv.DictReader(file)
            for row in reader:
                new_todo = Todo(text=row['text'])
                new_todo.done = True if row['done'] == 'true' else False
                new_todo.user_id = int(row['user_id'])
                db.add(new_todo)
            db.commit()
        print("Database Initialized")

@cli.command()
def list_todos():
    with get_cli_session() as db:
        data = []
        for todo in db.exec(select(Todo)).all():
            data.append([
                todo.text, 
                todo.done, 
                todo.user.username,
                todo.get_cat_list() if hasattr(todo, 'get_cat_list') else ""
            ])
        print(tabulate(data, headers=["Text", "Done", "User", "Categories"]))

@cli.command()
def create_user():
    """Create a new user interactively"""
    username = input("Username: ")
    email = input("Email: ")
    password = input("Password: ")
    
    with get_cli_session() as db:
        existing = db.exec(select(RegularUser).where(
            (RegularUser.username == username) | (RegularUser.email == email)
        )).first()
        if existing:
            print("User with that username or email already exists!")
            return
        user = RegularUser(
            username=username,
            email=email,
            password=encrypt_password(password)
        )
        db.add(user)
        db.commit()
        print(f"User {username} created successfully!")

@cli.command()
def list_users():
    """List all users"""
    with get_cli_session() as db:
        users = db.exec(select(RegularUser)).all()
        data = [[u.id, u.username, u.email, u.role] for u in users]
        print(tabulate(data, headers=["ID", "Username", "Email", "Role"]))

if __name__ == "__main__":
    cli()