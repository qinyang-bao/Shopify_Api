from flask import Blueprint

bp = Blueprint('api', __name__)

from flask_restful import Api
from App.api import resources
from App.api.resources import UsersAPI, ShopsAPI, ProductsAPI, OrdersAPI, LineItemsAPI

API = Api()
API.add_resource(UsersAPI, '/users', endpoint='user')
API.add_resource(ShopsAPI, '/shops', endpoint='shop')
API.add_resource(ProductsAPI, '/products', endpoint='product')
API.add_resource(OrdersAPI, '/orders', endpoint='order')
API.add_resource(LineItemsAPI, '/line_items', endpoint='line_item')

API.init_app(bp)

