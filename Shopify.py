from App import create_app
from App.models import Users

# create the flask app
app = create_app()

if __name__ == "__main__":
    app.run()
