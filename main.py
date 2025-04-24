from flask import Flask
from data import db_session

app = Flask(__name__)
app.config["SECRET_KEY"] = "produs_private_key"


def main():
    db_session.global_init("db/produs.db")
    app.run()


@app.route("/")
def index():
    pass


if __name__ == "__main__":
    main()
