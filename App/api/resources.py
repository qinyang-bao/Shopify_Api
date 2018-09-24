from App import db
from App.models import Users, Shops, Products, Orders, LineItems
from flask_restful import Resource, reqparse, inputs


class UsersAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type=str, required=True, help='No access key provided', location='args')
        self.reqparse.add_argument('id', type=int, location='args')
        self.reqparse.add_argument('list', type=bool, location='args')

        self.reqparse.add_argument('username', type=str, location='form')
        self.reqparse.add_argument('email', type=str, location='form')
        self.reqparse.add_argument('premium_level', type=str, location='form')

        super(UsersAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['id'] and not user.admin:
            return {'error': "this request is reserved for administrator"}, 403

        if args['list'] and not user.admin:
            return {'error': "this request is reserved for administrator"}, 403

        # returns a json object that contains all pertained information of the user
        def get_user(u):
            return {"name": u.user_name,
                    "id": u.id,
                    "email": u.email,
                    "access_key": u.access_key,
                    "premium_level": u.premium_level,
                    "is_admin": u.admin,
                    "owned_shops": [{'name': shop.shop_name, 'id': shop.id}
                                    for shop in Shops.query.filter_by(user_id=u.id).all()]

                    }

        if args['id']:
            user = Users.query.filter_by(id=args['id']).first()
            if user is None:
                return {'error': "key doesn't exist"}, 404

            return get_user(user), 200

        if args['list']:
            users = Users.query.all()
            response = {"users": []}
            for u in users:
                response["users"].append(get_user(u))

            return response, 200

        return get_user(user), 200

    def post(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['username'] is None or args['email'] is None or args['premium_level'] is None:
            return {"error": "missing arguments to create user"}, 400

        key, user_id = Users.create_user(args['username'], args['email'], args['premium_level'])
        if key:
            return {"created_user": args['username'],
                    "id": user_id,
                    "email": args['email'],
                    "premium_level": args['premium_level'],
                    'access_key': key}, 201
        else:
            return {"error": "user already exist. please use different email or name"},  409

    def put(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['id'] and not user.admin:
            return {'error': "this request is reserved for administrator"}, 403

        if args["id"] and user.admin:
            user = Users.query.filter_by(id=args['id']).first()

            if user is None:
                return {'error': "user with id {} doesn't exist".format(str(args['id']))}, 404

        if args['username'] is not None:
            _u = Users.query.filter_by(user_name=args['username']).first()
            if _u is not None:
                return {'error': "username already exists, please use a different one"}, 409
            user.user_name = args['username']

        if args['email'] is not None:
            _u = Users.query.filter_by(email=args['email']).first()
            if _u is not None:
                return {'error': "email already exists, please use a different one"}, 409
            user.email = args['email']

        if args['premium_level'] is not None:
            if not user.admin:
                return {'error': "this request is reserved for administrator"}, 403
            user.premium_level = args['premium_level']

        db.session.add(user)
        db.session.commit()

        return {
            "updated_user": args['username'],
            "id": user.id,
            "email": args['email'],
            "access_key": user.access_key,
            "premium_level": args['premium_level'],
        }, 200

    def delete(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if not user.admin:
            return {'error': "this request is reserved for administrator"}, 403

        if args["id"] is None:
            return {"error": "must specify id of the user to delete"},  400

        user = Users.query.filter_by(id=args['id']).first()
        if user is None:
            return {'error': "user with id {} doesn't exist".format(str(args['id']))}, 404

        # a copy of the user, so we can still access the attribute of user after it's being deleted
        _user = user
        db.session.delete(user)
        db.session.commit()

        return {
                   "deleted_user": _user.user_name,
                   "id": _user.id,
                   "email": _user.email,
                   "access_key": _user.access_key,
                   "premium_level": _user.premium_level
               }, 200


class ShopsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type=str, required=True, help='No access key provided', location='args')
        self.reqparse.add_argument('id', type=int, location='args')
        self.reqparse.add_argument('list', type=bool, location='args')

        self.reqparse.add_argument('shop_name', type=str, location='form')
        self.reqparse.add_argument('owner', type=str, location='form')

        super(ShopsAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()
        shop = Shops.query.filter_by(user_id=user.id).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if shop is None and not user.admin:
            return {"error": "this user does not own any shop"}, 404

        if not args['list'] and args['id'] is None:
            return {'error': "you must specify which shop(s) you want to get"}, 400

        # returns a json object that contains all pertained information of the shop
        def get_shop(s):
            return {"name": s.shop_name,
                    "id": s.id,
                    "owner": Users.query.filter_by(id=s.user_id).first().user_name,
                    "products": [{'name': product.product_name, 'id': product.id}
                                 for product in Products.query.filter_by(shop_id=s.id).all()],
                    "orders": [order.id for order in Orders.query.filter_by(shop_id=s.id).all()]
                    }

        if args['id']:
            shop = Shops.query.filter_by(id=args['id']).first()
            if shop is None:
                return {'error': "shop doesn't exist"}, 404

            if not shop.user_id == user.id and not user.admin:
                return {"error": "you cannot access shops that you do not own"}, 403

            return get_shop(shop), 200

        if args['list']:
            if user.admin:
                shops = Shops.query.all()
            else:
                shops = user.owned_shops()
            response = {"shops": []}
            for s in shops:
                response["shops"].append(get_shop(s))

            return response, 200

        return get_shop(shop), 200

    def post(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['shop_name'] is None:
            return {"error": "missing arguments to create shop"}, 400

        if args['owner'] is None:
            shop_owner = user
        else:
            shop_owner = Users.query.filter_by(user_name=args['owner']).first()
            if shop_owner is None:
                return {'error': "the user {} doesn't exist".format(str(args['owner']))}, 404

        if not user.evaluate_premimum("create shop"):
            return {"error": "Premium level too low for this operation"}, 403

        shop_id = Shops.create_shop(args['shop_name'], shop_owner)
        if shop_id:
            return {"created_shop": args['shop_name'],
                    "id": shop_id,
                    "owner": args['owner']
                    }, 201
        else:
            return {"error": "shop already exist. please use different name"},  409

    def put(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which shop you want to update"},  400

        def update_shop(_shop, _shop_name=None, _owner_name=None):
            if _shop_name is not None:
                _s = Shops.query.filter_by(shop_name=_shop_name).first()
                if _s is not None:
                    return {'error': "shop name already exists, please use a different one"}, 409
                _shop.shop_name = _shop_name

            if _owner_name is not None:
                owner = Users.query.filter_by(user_name=_owner_name).first()
                if owner is None:
                    return {'error': "user {} does not exist".format(str(_owner_name))}, 404
                _shop.user_id = owner.id

            db.session.add(_shop)
            db.session.commit()

            return {
                       "updated_shop": _shop_name,
                       "id": shop.id,
                       "owner": _owner_name
                   }, 200

        shop = Shops.query.filter_by(id=args['id']).first()
        if shop is not None:
            if not shop.user_id == user.id:
                if not user.admin:
                    return {"error": "You cannot update shop that you do not own"}, 403
                else:
                    return update_shop(shop, args["shop_name"], args['owner'])
            else:
                # does not allow users that are not the administrator to change shop owner
                return update_shop(shop, args["shop_name"])

        else:
            return {'error': "shop with id {} doesn't exist".format(str(args['id']))}, 404

    def delete(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which shop you want to delete"},  400

        def delete_shop(shop):
            # a copy of the shop, so we can still access the attributes of shop after it's being deleted
            _shop = shop
            db.session.delete(shop)
            db.session.commit()

            return {
                       "deleted_shop": _shop.shop_name,
                       "id": _shop.id,
                       # no need to check if the user exists, since a shop will always have an owner
                       "owner": Users.query.filter_by(id=_shop.user_id).first().user_name
                   }

        shop = Shops.query.filter_by(id=args['id']).first()
        if shop is not None:
            if not shop.user_id == user.id:
                if not user.admin:
                    return {"error": "You cannot delete shops that you do not own"}, 403
                else:
                    return delete_shop(shop), 200
            else:
                return delete_shop(shop), 200

        else:
            return {'error': "shop with id {} doesn't exist".format(str(args['id']))}, 404


class ProductsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type=str, required=True, help='No access key provided', location='args')
        self.reqparse.add_argument('id', type=int, location='args')
        self.reqparse.add_argument('shop_id', type=int, location='args')
        self.reqparse.add_argument('list', type=bool, location='args')

        self.reqparse.add_argument('product_name', type=str, location='form')
        self.reqparse.add_argument('store', type=str, location='form')
        self.reqparse.add_argument('price', type=float, location='form')
        self.reqparse.add_argument('cost', type=float, location='form')

        super(ProductsAPI, self).__init__()

    # three modes of get:
    # get by id of the product
    # list all products in a store by shop id
    # list all products
    def get(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        count = 0
        if args['id']:
            count += 1
        if args['shop_id']:
            count += 1
        if args['list']:
            count += 1
        if count > 1:
            return {'error': "ambiguous request, you can only use one of id, shop id, or list"}, 400
        if count == 0:
            return {'error': "you must specify which product(s) you want to get"}, 400

        # returns a json object that contains all pertained information of the product
        def get_product(p):
            data = {"name": p.product_name,
                    "id": p.id,
                    "store": Shops.query.filter_by(id=p.shop_id).first().shop_name,
                    "cost": p.cost,
                    "line_items": [item.id for item in LineItems.query.filter_by(product_id=p.id).all()]
                    }

            total_income = 0
            average_price = 0
            total_quantity = 0
            for item in data['line_items']:
                item = LineItems.query.filter_by(id=item).first()
                total_income += (item.unit_price - data["cost"]) * item.quantity
                average_price += item.unit_price
                total_quantity += item.quantity

            data["average_price"] = average_price / len(data["line_items"])
            data["total_income"] = total_income
            return data

        if args['id']:
            product = Products.query.filter_by(id=args['id']).first()
            if product is None:
                return {'error': "product doesn't exist"}, 404

            if user.admin:
                return get_product(product), 200

            else:
                shop_ids = user.owned_shop_ids()
                if product.shop_id not in shop_ids:
                    return {'error': "you cannot access products that are not in your shops"}, 403
                return get_product(product), 200

        if args['shop_id']:
            products = Products.query.filter_by(shop_id=args['shop_id']).all()
            if len(products) == 0:
                return {'error': "no products in this shop"}, 404
            response = {"products": []}

            if user.admin:
                for p in products:
                    response["products"].append(get_product(p))
                return response, 200

            else:
                shop_ids = user.owned_shop_ids()
                if args["shop_id"] not in shop_ids:
                    return {'error': "you cannot access products that are not in your shops"}, 403
                for p in products:
                    response["products"].append(get_product(p))
                return response, 200

        if args['list']:
            response = {"products": []}
            if user.admin:
                products = Products.query.all()
                for p in products:
                    response["products"].append(get_product(p))
                return response, 200
            else:
                products = user.owned_products()
                for p in products:
                    response["products"].append(get_product(p))
                return response, 200

    def post(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['product_name'] is None or args["store"] is None or args["cost"] is None or args["price"] is None:
            return {"error": "missing arguments to create product"}, 400

        shop = Shops.query.filter_by(shop_name=args['store']).first()
        if shop is None:
            return {'error': "shop for which the product is to be added does not exist"}, 404

        if not user.evaluate_premimum("add product"):
            return {"error": "Premium level too low for this operation"}, 403

        def create_product(_name, _shop, _price, _cost):
            product_id = Products.create_product(_name, _shop, _price, _cost)
            if product_id:
                return {"created_product": args['product_name'],
                        "id": product_id,
                        "store": args['store'],
                        "price": args["price"],
                        "cost": args["cost"]
                        }, 200
            else:
                return {"error": "product already exists. please use different name"}, 409

        shop_ids = user.owned_shop_ids()
        if shop.id not in shop_ids:
            if not user.admin:
                return {"errpor": "the store of the product must be a shop that you own"}, 403

        return create_product(args['product_name'], shop, args["price"], args["cost"])

    def put(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which product you want to update"},  400

        def update_product(_product, _product_name=None, _product_store=None, _price=None, _cost=None):
            if _product_name is not None:
                _p = Products.query.filter(Products.shop_id == _product.id).filter(
                                           Products.product_name == _product_name).first()
                if _p is not None:
                    return {'error': "product name already exists, please use a different one"}, 409
                _product.product_name = _product_name

            if _product_store is not None:
                _product.shop_id = _product_store.id

            if _price is not None:
                _product.price = _price

            if _cost is not None:
                _product.cost = _cost

            db.session.add(_product)
            db.session.commit()

            return {
                       "updated_product": _product_name,
                       "id": _product.id,
                       "store": _product.store.shop_name if _product_store is None else _product_store.shop_name,
                       "price": _price,
                       "cost": _cost
                   }, 200

        product = Products.query.filter_by(id=args['id']).first()
        store = Shops.query.filter_by(shop_name=args['store']).first()
        shop_ids = user.owned_shop_ids()
        if product is not None:
            if product.shop_id not in shop_ids:
                if not user.admin:
                    return {"error": "You cannot update product that you do not own"}, 403
                else:
                    return update_product(product, args["product_name"], store, args['price'], args['cost'])
            else:
                if store.id not in shop_ids:
                    return {"error": "You cannot update store of the product to a shop that you do not own"}, 403
                else:
                    return update_product(product, args["shop_name"], store, args['price'], args['cost'])

        else:
            return {'error': "product with id {} doesn't exist".format(str(args['id']))}, 404

    def delete(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which product you want to delete"},  400

        def delete_product(product):
            # a copy of the product, so we can still access the attributes of the product after it's being deleted
            _product = product
            db.session.delete(product)
            db.session.commit()

            return {
                        "deleted_product": _product.product_name,
                        "id": _product.id,
                        # no need to check if the store exists, since a product will always have an owner
                        "store": Shops.query.filter_by(id=_product.shop_id).first().shop_name,
                        "price": _product.price,
                        "cost": _product.cost
                   }

        product = Products.query.filter_by(id=args['id']).first()
        shop_ids = user.owned_shop_ids()
        if product is not None:
            if product.shop_id not in shop_ids:
                if not user.admin:
                    return {"error": "You cannot delete product that you do not own"}, 403
                else:
                    return delete_product(product), 200
            else:
                return delete_product(product), 200

        else:
            return {'error': "product with id {} doesn't exist".format(str(args['id']))}, 404


class OrdersAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type=str, required=True, help='No access key provided', location='args')
        self.reqparse.add_argument('id', type=int, location='args')
        self.reqparse.add_argument('shop_id', type=int, location='args')
        self.reqparse.add_argument('list', type=bool, location='args')

        self.reqparse.add_argument('store', type=str, location='form')

        super(OrdersAPI, self).__init__()

    # three modes of get:
    # get by id of the product
    # list all products in a store by shop id
    # list all products
    def get(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        count = 0
        if args['id']:
            count += 1
        if args['shop_id']:
            count += 1
        if args['list']:
            count += 1
        if count > 1:
            return {'error': "ambiguous request, you can only use one of id, shop id, or list"}, 400
        if count == 0:
            return {'error': "you must specify which order(s) you want to get"}, 400

        # returns a json object that contains all pertained information of the product
        def get_order(o):
            data = {
                    "id": o.id,
                    "store": Shops.query.filter_by(id=o.shop_id).first().shop_name,
                    "line_items": [item.id for item in LineItems.query.filter_by(order_id=o.id).all()]
                    }
            total_price = 0
            total_cost = 0
            total_income = 0
            for item_id in data["line_items"]:
                item = LineItems.query.filter_by(id=item_id).first()
                total_price += item.unit_price * item.quantity
                total_cost += item.type.cost * item.quantity
                total_income += (item.unit_price - item.type.cost) * item.quantity

            data["total_price"] = total_price
            data["total_cost"] = total_cost
            data["total_income"] = total_income

            return data

        if args['id']:
            order = Orders.query.filter_by(id=args['id']).first()
            if order is None:
                return {'error': "product doesn't exist"}, 404

            if user.admin:
                return get_order(order), 200

            else:
                shop_ids = user.owned_shop_ids()
                if order.shop_id not in shop_ids:
                    return {'error': "you cannot access orders that are not from your shops"}, 403
                return get_order(order), 200

        if args['shop_id']:
            orders = Orders.query.filter_by(shop_id=args['shop_id']).all()
            if len(orders) == 0:
                return {'error': "no orders in this shop"}, 404
            response = {"orders": []}

            if user.admin:
                for o in orders:
                    response["orders"].append(get_order(o))
                return response, 200

            else:
                shop_ids = user.owned_shop_ids()
                if args["shop_id"] not in shop_ids:
                    return {'error': "you cannot access products that are not in your shops"}, 403
                for o in orders:
                    response["orders"].append(get_order(o))
                return response, 200

        if args['list']:
            response = {"orders": []}
            if user.admin:
                orders = Orders.query.all()
                for o in orders:
                    response["orders"].append(get_order(o))
                return response, 200
            else:
                shop_ids = user.owned_shop_ids()
                orders = Orders.query.filter(Orders.shop_id.in_(shop_ids)).all()
                for o in orders:
                    response["orders"].append(get_order(o))
                return response, 200

    def post(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['store'] is None:
            return {"error": "missing arguments to create order"}, 400

        shop = Shops.query.filter_by(shop_name=args['store']).first()
        if shop is None:
            return {'error': "shop for which the order is to be added does not exist"}, 404

        if not user.evaluate_premimum("add order"):
            return {"error": "Premium level too low for this operation"}, 403

        def create_order(_shop):
            order_id = Orders.create_order(_shop)
            return {"created_order": order_id,
                    "store": args['store'],
                    }, 200

        shop_ids = user.owned_shop_ids()
        if shop.id not in shop_ids:
            if not user.admin:
                return {"error": "the shop of the order must be a shop that you own"}, 403

        return create_order(shop)

    def put(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which order you want to update"},  400

        def update_order(_order,  _order_store=None):
            if _order_store is not None:
                _order.shop_id = _order_store.id

            db.session.add(_order)
            db.session.commit()

            return {
                       "updated_order": _order.id,
                       "store": _order.store.shop_name if _order_store is None else _order_store.shop_name
                   }, 200

        order = Orders.query.filter_by(id=args['id']).first()
        store = Shops.query.filter_by(shop_name=args['store']).first()
        shop_ids = user.owned_shop_ids()
        if order is not None:
            if order.shop_id not in shop_ids:
                if not user.admin:
                    return {"error": "You cannot update order that's not from your store"}, 403
                else:
                    return update_order(order, store)
            else:
                if store.id not in shop_ids:
                    return {"error": "You cannot update store of the order to a shop that you do not own"}, 403
                else:
                    return update_order(order, store)

        else:
            return {'error': "order with id {} doesn't exist".format(str(args['id']))}, 404

    def delete(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which order you want to delete"},  400

        def delete_order(order):
            # a copy of the order, so we can still access the attributes of the order after it's being deleted
            _order = order
            db.session.delete(order)
            db.session.commit()

            return {
                        "deleted_order": _order.id,
                        # no need to check if the store exists, since an order will always have an owner
                        "store": Shops.query.filter_by(id=_order.shop_id).first().shop_name
                   }

        order = Orders.query.filter_by(id=args['id']).first()
        shop_ids = user.owned_shop_ids()
        if order is not None:
            if order.shop_id not in shop_ids:
                if not user.admin:
                    return {"error": "You cannot delete an order that's not from one of your shops"}, 403
                else:
                    return delete_order(order), 200
            else:
                return delete_order(order), 200

        else:
            return {'error': "product with id {} doesn't exist".format(str(args['id']))}, 404


class LineItemsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type=str, required=True, help='No access key provided', location='args')

        self.reqparse.add_argument('id', type=int, location='args')
        self.reqparse.add_argument('shop_id', type=int, location='args')
        self.reqparse.add_argument('product_id', type=int, location='args')
        self.reqparse.add_argument('order_id', type=int, location='args')
        self.reqparse.add_argument('list', type=bool, location='args')

        self.reqparse.add_argument('order', type=int, location='form')
        self.reqparse.add_argument('type', type=str, location='form')
        self.reqparse.add_argument('price', type=float, location='form')
        self.reqparse.add_argument('quantity', type=int, location='form')

        super(LineItemsAPI, self).__init__()

    # five modes of get:
    # get by id of the product
    # list all items of a specific type by product id
    # list all items from a specific order by order id
    # list all products in a store by shop id
    # list all products
    def get(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        count = 0
        if args['id']:
            count += 1
        if args['product_id']:
            count += 1
        if args['order_id']:
            count += 1
        if args['shop_id']:
            count += 1
        if args['list']:
            count += 1
        if count > 1:
            return {'error': "ambiguous request, you can only use one of id, product id, order id, shop id, or list"}\
                , 400
        if count == 0:
            return {'error': "you must specify which line item(s) you want to get"}, 400

        # returns a json object that contains all pertained information of the line item
        def get_item(i):
            data = {
                    "id": i.id,
                    "product": Products.query.filter_by(id=i.product_id).first().product_name,
                    "order": Orders.query.filter_by(id=i.order_id).first().id,
                    "unit_price": i.unit_price,
                    "quantity": i.quantity
                    }

            data["total_price"] = data["unit_price"] * data["quantity"]
            order = Orders.query.filter_by(id=i.order_id).first()
            data["store"] = Shops.query.filter_by(id=order.shop_id).first().shop_name

            return data

        # get all valid order ids/ product ids that the line item could belong to for the user
        order_ids = user.owned_order_ids()
        product_ids = user.owned_product_ids()

        if args['id']:
            item = LineItems.query.filter_by(id=args['id']).first()
            if item is None:
                return {'error': "line item doesn't exist"}, 404

            if not user.admin:
                # if the order id of the line item is not one of the order ids that belong to this user
                if item.order_id not in order_ids:
                    return {'error': "you cannot access line items that are not from your shops"}, 403

            return get_item(item), 200

        if args['order_id']:
            items = LineItems.query.filter_by(order_id=args['order_id']).all()
            if len(items) == 0:
                return {'error': "no line items in this order or this order does not exist"}, 404
            response = {"line_items": []}

            if not user.admin:
                if args["order_id"] not in order_ids:
                    return {'error': "you cannot access line items that are not from your shops"}, 403
                items = LineItems.query.filter(LineItems.order_id.in_(order_ids)).all()

            for i in items:
                response["line_items"].append(get_item(i))
            return response, 200

        if args['product_id']:
            items = LineItems.query.filter_by(product_id=args['product_id']).all()
            if len(items) == 0:
                return {'error': "no line items for this product or this product does not exist"}, 404
            response = {"line_items": []}

            if not user.admin:
                if args["product_id"] not in product_ids:
                    return {'error': "you cannot access line items that are not from your shops"}, 403
                items = LineItems.query.filter(LineItems.product_id.in_(product_ids)).all()

            for i in items:
                response["line_items"].append(get_item(i))
            return response, 200

        if args['shop_id']:
            shop = Shops.query.filter_by(id=args['shop_id']).first()
            if shop is None:
                return {'error': "shop with this id does not exist"}, 404
            shop_ids = user.owned_shop_ids()
            items = shop.owned_items()

            if len(items) == 0:
                return {'error': "no line items in this shop"}, 404

            response = {"line_items": []}
            if not user.admin:
                if args["shop_id"] not in shop_ids:
                    return {'error': "you cannot access products that are not in your shops"}, 403

            for i in items:
                response["orders"].append(get_item(i))
            return response, 200

        if args['list']:
            items = LineItems.query.all()

            response = {"line_items": []}
            if not user.admin:
                items = user.owned_items()

            for i in items:
                response["line_items"].append(get_item(i))
            return response, 200

    def post(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args['order'] is None or args["type"] is None or args["price"] is None or args["quantity"] is None:
            return {"error": "missing arguments to create order"}, 400

        product = Products.query.filter_by(product_name=args['type']).first()
        if product is None:
            return {'error': "the product type for which the line item is to be put under does not exist"}, 404

        order = Orders.query.filter_by(id=args['order']).first()
        if order is None:
            return {'error': "the order for which the line item is to be put under does not exist"}, 404

        if not user.evaluate_premimum("add line item"):
            return {"error": "Premium level too low for this operation"}, 403

        def create_item(_product, _order, _price, _quantity):
            item_id = LineItems.create_line_item(_product, _order, _price, _quantity)

            return {"created_line_item": item_id,
                    "product": args['type'],
                    "order": args['order'],
                    "unit_price": args["price"],
                    "quantity": args["quantity"]
                    }, 200

        products = user.owned_products()
        orders = user.owned_orders()

        if order not in orders:
            if not user.admin:
                return {"error": "You cannot create a line item with an order that's not from your store"}, 403
            else:
                return create_item(product, order, args['price'], args['quantity'])
        else:
            if product not in products:
                return {"error": "You cannot create a line item of a product type that's not from your store"}, 403
            else:
                return create_item(product, order, args['price'], args['quantity'])

    def put(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which line item you want to update"},  400

        def update_item(_item,  _product=None, _order=None, _price=None, _quantity=None):
            if _product is not None:
                _item.product_id = _product.id

            if _order is not None:
                _item.order_id = _order.id

            if _price is not None:
                _item.unit_price = _price

            if _quantity is not None:
                _item.quantity = _quantity

            db.session.add(_item)
            db.session.commit()

            return {
                       "updated_line_item": _item.id,
                       "product": _product.product_name if _product is not None else Products.query.filter_by
                       (id=_item.id).first(),
                       "order": _order.id if _order is not None else _item.order_id,
                       "unit_price": _price if _price is not None else _item.unit_price,
                       "quantity": _quantity if _quantity is not None else _item.quantity,
                   }, 200

        item = LineItems.query.filter_by(id=args['id']).first()
        product = Products.query.filter_by(product_name=args['type']).first()
        order = Orders.query.filter_by(id=args['order']).first()

        products = user.owned_products()
        orders = user.owned_orders()

        if item is not None:
            if item.type not in products:
                if not user.admin:
                    return {"error": "You cannot update order that's not from your store"}, 403
                else:
                    return update_item(item, product, order, args['price'], args['quantity'])
            else:
                if product not in products:
                    return {"error": "You cannot update product type of the line order to a product type that "
                                     "you do not own"}, 403
                if order not in orders:
                    return {"error": "You cannot update order which the line order belongs to to a product type that "
                                     "you do not own"}, 403
                else:
                    return update_item(item, product, order, args['price'], args['quantity'])

        else:
            return {'error': "item with id {} doesn't exist".format(str(args['id']))}, 404

    def delete(self):
        args = self.reqparse.parse_args()
        user = Users.query.filter_by(access_key=args["key"]).first()

        if user is None:
            return {'error': "key doesn't exist"}, 404

        if args["id"] is None:
            return {"error": "you must specify which line item you want to delete"},  400

        def delete_item(item):
            # a copy of the item, so we can still access the attributes of the item after it's being deleted
            _item = item
            db.session.delete(item)
            db.session.commit()

            return {
                       "deleted_line_item": _item.id,
                       # we do not need to worry if the product is None since all line items would have a product type
                       "product": Products.query.filter_by(id=_item.product_id).first().product_name,
                       "order": _item.order_id,
                       "unit_price": _item.unit_price,
                       "quantity": _item.quantity,
                   }

        item = LineItems.query.filter_by(id=args['id']).first()
        products = user.owned_products()

        if item is not None:
            if item.type not in products:
                if not user.admin:
                    return {"error": "You cannot delete an item that's not from one of your shops"}, 403
                else:
                    return delete_item(item), 200
            else:
                return delete_item(item), 200

        else:
            return {'error': "line item with id {} doesn't exist".format(str(args['id']))}, 404
