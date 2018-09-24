from App import db
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import random, string


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    access_key = db.Column(db.String(15), index=True, nullable=False)
    # account premium level ---> could be used later to enable premium business model
    premium_level = db.Column(db.Integer, nullable=False, default=0)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    shops = db.relationship('Shops', backref='owner', lazy='dynamic', cascade="save-update, merge, delete")

    def __repr__(self):
        return '<User {}>'.format(self.user_name)

    # we could fill this function later to enable premium business model
    # ex. each level of premium can own different number of shops etc.
    def evaluate_premimum(self, action=""):
        return True

    def owned_shops(self):
        return Shops.query.filter_by(user_id=self.id).all()

    def owned_shop_ids(self):
        return [shop.id for shop in self.owned_shops()]

    def owned_products(self):
        shops_ids = self.owned_shop_ids()
        return Products.query.filter(Products.shop_id.in_(shops_ids)).all()

    def owned_product_ids(self):
        return [product.id for product in self.owned_products()]

    def owned_orders(self):
        shops_ids = self.owned_shop_ids()
        return Orders.query.filter(Orders.shop_id.in_(shops_ids)).all()

    def owned_order_ids(self):
        return [product.id for product in self.owned_orders()]

    def owned_items(self):
        product_ids = self.owned_product_ids()
        order_ids = self.owned_order_ids()
        p_items = LineItems.query.filter(LineItems.product_id.in_(product_ids)).all()
        items = LineItems.query.filter(LineItems.order_id.in_(order_ids)).all()

        for i in p_items:
            is_duplicated = False
            for _i in items:
                if i.id == _i.id:
                    is_duplicated = True
                    break
            if not is_duplicated:
                items.append(i)

        return items

    def owned_item_ids(self):
        return [item.id for item in self.owned_items()]

    @staticmethod
    def create_user(name, email, premium_level=1, admin=False, key=None):
        user = Users.query.filter(Users.user_name == name or Users.email == email).first()
        if user is not None:
            return False

        # create a non existing random access key
        if key is None:
            while True:
                key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(15)])
                u = Users.query.filter_by(access_key=key).first()
                if u is None:
                    break

        user = Users(user_name=name, email=email, access_key=key, premium_level=premium_level, admin=admin)
        db.session.add(user)
        db.session.commit()
        return key, user.id


class Shops(db.Model):
    __tablename__ = "shops"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shop_name = db.Column(db.String(64), nullable=False, unique=True)

    products = db.relationship('Products', backref='store', lazy='dynamic', cascade="save-update, merge, delete")
    orders = db.relationship('Orders', backref='store', lazy='dynamic', cascade="save-update, merge, delete")

    def __repr__(self):
        return '<Shop {}>'.format(self.shop_name)

    def owned_items(self):
        product_ids = [product.id for product in Products.query.filter_by(shop_id=self.id).all()]
        order_ids = [order.id for order in Orders.query.filter_by(shop_id=self.id).all()]
        p_items = LineItems.query.filter(LineItems.product_id.in_(product_ids)).all()
        items = LineItems.query.filter(LineItems.order_id.in_(order_ids)).all()

        for i in p_items:
            is_duplicated = False
            for _i in items:
                if i.id == _i.id:
                    is_duplicated = True
                    break
            if not is_duplicated:
                items.append(i)

        return items

    def owned_item_ids(self):
        return [item.id for item in self.owned_items()]

    @staticmethod
    def create_shop(name, owner):
        shop = Shops.query.filter(Shops.shop_name == name).first()
        if shop is not None:
            return False

        shop = Shops(shop_name=name, user_id=owner.id)
        db.session.add(shop)
        db.session.commit()
        return shop.id


class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    product_name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False, index=True)
    cost = db.Column(db.Float, nullable=False, index=True)

    line_items = db.relationship('LineItems', backref='type', lazy='dynamic', cascade="save-update, merge, delete")

    def __repr__(self):
        return '<Products {}>'.format(self.product_name)

    @staticmethod
    def create_product(name, store, price, cost):
        product = Products.query.filter(Products.shop_id == store.id).filter(Products.product_name == name).first()
        if product is not None:
            return False

        product = Products(product_name=name, shop_id=store.id, price=price, cost=cost)
        db.session.add(product)
        db.session.commit()
        return product.id


class Orders(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)

    # instead of storing these attributes in the database, we will calculate them in run time, to reduce the number
    # of changes made to the database (else, when one makes a change to line items, products, etc, these values all
    # need to be recalculated

    # total_price = db.Column(db.Float, nullable=False, index=True)
    # total_cost = db.Column(db.Float, nullable=False, index=True)
    # total_income = db.Column(db.Float, nullable=False, index=True)

    lineItems = db.relationship('LineItems', backref='bill', lazy='dynamic', cascade="save-update, merge, delete")

    def __repr__(self):
        return '<Order {}>'.format(self.id)

    @staticmethod
    def create_order(store):
        order = Orders(shop_id=store.id)
        db.session.add(order)
        db.session.commit()
        return order.id


class LineItems(db.Model):
    __tablename__ = "line_items"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    unit_price = db.Column(db.Float, nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False, index=True)

    def __repr__(self):
        return '<LineItem {}>'.format(self.id)

    @staticmethod
    def create_line_item(product, order, price, quantity):
        item = LineItems(product_id=product.id, order_id=order.id, unit_price=price, quantity=quantity)
        db.session.add(item)
        db.session.commit()
        return item.id

