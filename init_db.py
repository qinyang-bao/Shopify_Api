from App import create_app, db
from App.models import Users, Shops, Products, Orders, LineItems

# create the flask app
app = create_app()


# populate the database with an admin
def set_up():
    with app.app_context():
        if Users.create_user("Qinyang", "q7bao@edu.uwaterloo.ca", 5, True, app.config["ADMIN_KEY"]):
            # if this returns true, would mean that it is the first time that this web app is running, so we populate
            # some testing data
            Users.create_user("Waterloo", "shop@uwaterloo.ca", 1, False)
            waterloo = Users.query.filter_by(user_name="Waterloo").first()

            Shops.create_shop("Waterloo bookstore", waterloo)
            bookstore = Shops.query.filter_by(shop_name="Waterloo bookstore").first()

            Products.create_product("MTE 140", bookstore, 100, 10)
            MTE_140 = Products.query.filter_by(product_name="MTE 140").first()

            Orders.create_order(bookstore)
            first_order = Orders.query.filter_by(id=1).first()

            LineItems.create_line_item(MTE_140, first_order, 100, 2)


def tear_down():
    with app.app_context():
        all_data = [Users.query.all(), Shops.query.all(), Products.query.all(), Orders.query.all(),
                    LineItems.query.all()]
        for table in all_data:
            for row in table:
                db.session.delete(row)

        db.session.commit()


tear_down()
set_up()