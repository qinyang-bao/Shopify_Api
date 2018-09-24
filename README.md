# Shopify API


## Overview:
This is a simple server-side web API that might be used by E-commerce companies like Shopify.
It models the following relationship:  
- Users have many shops   
- Shops have many Products  
- Shops have many Orders  
- Products have many Line Items  
- Orders have many Line Items  

Each resource has full CURD operations implemented. 
   
Users would have a key, corresponding to its identity. Different key would have different access privilege. There is a 
key for the administrator which has the highest privilege, it may get, create, update, delete any resources. Meanwhile, 
normal user keys may only change resources associated to itself.  
  
Line items refer to any service or product added to an order, along with the quantity and price that pertain to them.
For example, if you buy a carton of milk and two loaf of bread at the grocery store, your bill (the representation of 
your order) will have two line items on it. One for the carton of milk, and the other for two loafs of bread.
  
  
#### Todo && In Progress:
- Deploy with Docker and GKE
- Add pagination for listing resources
- Implement usage limit or other limiting measures for premium business model
- More thorough testing
- Optimize queries and clean up code (use join query)
  
  
## Installation:
Make sure you have:
```
python 3.6.5 and above
```

On Linux, simply execute the setup.sh script:
```
$ git clone https://github.com/qinyang-bao/Shopify_Api.git
$ ./setup.sh
```

On Windows:
```
$ git clone https://github.com/qinyang-bao/Shopify_Api.git
$ python3 -m venv venv
$ venv\Scripts\activate
$ (venv) pip install -r requirements.txt
```

There is a sample.env file that you may want to change the env vars to the ones that suit your need, then rename it to .env.  
I have also included a sample sqlite database file in the repository that does not require any additional setup. But you 
may also use other databases server(eg. MySQL). To do that, first create a database (remember to change the), then:
```
$ source venv/bin/activate (or if you are on Windows: venv\Scripts\activate)
$ (venv) set FLASK_APP=Shopify.py
$ (venv) flask db upgrade
```

## Usage:
I will discuss the usage of this API by going over each resource (users, shops, products, orders, line_items). 
You may use curl or the request library of python.  

All request would follow the following basic structure:  
http://127.0.0.1:5000/api/v1/<resource_name>?key=<key>&<other_params>=<value>  
Typically, the parameters in the url are for specifying/locating the resource (eg.id, key).  
Meanwhile, in the body of the request, you would also include arguments which are typically actual information of the resource
(eg. name, price, owner, etc.) You would only need to use the body for POST and PUT requests.  

For your convenience, the  sqlite database included (app.db) is populated with some sample data. It contains two users,
one is the administrator, the other is "Waterloo". There is one shop "Waterloo bookstore", owned by "Waterloo". The shop
has one product "MTE 140" and one single order. There is one line item, which is two "MTE 140" and it is on the first order.  

The administrator key is "a12b1e7128dged4" which would give you unlimited access of the api.

 
####users:  
######GET (read)  
http://127.0.0.1:5000/api/v1/users?key={key}&id={id}&list={true}
- parameter "key" is the user key
- parameter "id" and "list" are reserved for administrator
- specify "id" to get the user information of the user with this id
- set "list' to true to list all users
- if does not use "list" and "id" parameter (what a normal user would do), return the information of 
own user (identified by the key) 

If only one user information is requested, would return a jason object that contains these attributes:
- name: username
- id: user id
- email: user email
- access_key: user key
- premium_level: level of premium, access privilege 
- is_admin: a boolean indicating whether the user is the administrator or not
- owned_shops: a list of shops owned by the user. each item in the list is an object that contains attributes: 
    - name: name of the store
    - id: id of the store
  
If multiple users information is requested, the returned json would be:
- users: a list of user object, each would have the above described attributes 

#####POST (create)
http://127.0.0.1:5000/api/v1/users?key={key}
Body: username={username}&email={email}&premium_level={premium_level}
- parameter "key" is the user key. Only the administrator (identified by key) may create a user
- argument "username", "email", and "premium_level" must all be present (what they do is self-explanatory)

The returned json object would contain the attributes:
- created_user: username
- id: user id
- email: user email
- access_key: user key
- premium_level: level of premium, access privilege  
  
You may notice that it does not include "owned_shops" as the GET request would return, this is because when a user is
first created, of course it would not have any owned shops. Also, for the response of POST method, I am trying to make
it only contain the information about the created resource, excluding information of related resources. I will be keep using 
this design for the PUT and DELETE request as well. This design is the same for all other resources as well.


#####PUT (update)
http://127.0.0.1:5000/api/v1/users?key={key}&id={id}
Body: username={username}&email={email}&premium_level={premium_level}
- parameter "key" is the user key. 
- parameter "id" is the id of the user to update, only the administrator may use this parameter
- argument "username", "email", and "premium_level" may not need to be all present, only the present ones will be used to update
the associated attribute
    - Only the administrator may change the premium level of a user  
  
The returned json object would contain the attributes:
- updated_user: username
- id: user id
- email: user email
- access_key: user key
- premium_level: level of premium, access privilege

#####DELETE (delete)
http://127.0.0.1:5000/api/v1/users?key={key}&id={id}
- parameter "key" is the user key, only the administrator may use this request
- parameter "id" is the id of the user to delete
  
The returned json object would contain the attributes:
- updated_user: username
- id: user id
- email: user email
- access_key: user key
- premium_level: level of premium, access privilege  
  
   
 
###Shops:
#####GET (read)
http://127.0.0.1:5000/api/v1/shops?key=<key>&id=<id>&list=<true>
- parameter "key" is the user key
- parameter "id" specifies which shop's information to get. Administrator may use any id, normal user can only use id of
shops that he/she own
- set parameter "list" to true to obtain a list of shops. Administrator would get all shops, normal user would only get 
shops that he/she own

If only one shop's information is requested, would return a jason object that contains these attributes:
- name: shop name
- id: shop id
- owner: user name of the owner of the shop
- products: a list of products in the shop, each item in the list is an object that contains attributes: 
    - name: name of the product
    - id: id of the id
- orders: a list of orders from the shop, each item is the id of the order  
    
If multiple shops' information is requested, the returned json would be:
- shops: a list of shop object, each would have the above described attributes 

#####POST (create)
http://127.0.0.1:5000/api/v1/shops?key=<key>
Body: shop_name=<username>&owner=<username of the user that owns this shop>
- parameter "key" is the user key. 
- argument "shop_name" and "owner" must all be present (what they do is self-explanatory)

The returned json object would contain the attributes:
- created_shop: shop name
- id: shop id
- owner: user name of the owner of the shop

#####PUT (update)
http://127.0.0.1:5000/api/v1/shops?key=<key>&id=<id>
Body: username=<username>&email=<email>&premium_level=<premium_level>
- parameter "key" is the user key. 
- parameter "id" is the id of the shop to update. Administrator may update any shops, normal users can only update their own shop(s)
- argument "shop_name" and "owner" may not need to be all present, only the present ones will be used to update the associated attribute   
  
The returned json object would contain the attributes:
- updated_shop: shop name
- id: shop id
- owner: user name of the owner of the shop  
  
#####DELETE (delete)
http://127.0.0.1:5000/api/v1/shops?key=<key>&id=<id>
- parameter "key" is the user key
- parameter "id" is the id of the shop to delete. Administrator may delete any shops, normal users can only delete their own shop(s)
  
The returned json object would contain the attributes:
- deleted_shop: shop name
- id: shop id
- owner: user name of the owner of the shop  
  
  

###Products:
#####GET (read)
http://127.0.0.1:5000/api/v1/products?key=<key>&id=<id>&shop_id=<shop_id>&list=<true>
- parameter "key" is the user key
- parameter "id" specifies which product's information to get. Administrator may use any id, normal user can only use id of
products from shops that he/she own
- parameter "shop_id" specifies which shop's products' information to get. Administrator may use any id, normal user can only use the id of
shops that he/she own
- set parameter "list" to true to obtain a list of products. Administrator would get all products, normal user would only get 
products from shops that he/she own

If only one product's information is requested, would return a jason object that contains these attributes:
- name: product name
- id: product id
- store: shop name of the store which has this product 
- cost: cost of this product (cost in the sense that price-cost=income)
- line_items: a list of the ids of line items of this product type
- average_price: average selling price of this product, derived from the sold price indicated in each line item  
(line items may have different selling price) 
- total_income: total income obtained from selling this product, derived from cost and line item sold price  
    
If multiple products' information is requested, the returned json would be:
- products: a list of product object, each would have the above described attributes 

#####POST (create)
http://127.0.0.1:5000/api/v1/products?key=<key>
Body: product_name=<username>&store=<name of the shop that this product is in>&price=<normal price of the product>&cost=<cost>
- parameter "key" is the user key. 
- argument "product_name", "store", "price", "cost" must all be present (what they do is self-explanatory)
    - The store must be owned by the user, unless the user is the administrator

The returned json object would contain the attributes:
- created_product: product name
- id: product id
- store: shop name of the shop that this product is in
- price: product normal price
- cost: product cost

#####PUT (update)
http://127.0.0.1:5000/api/v1/products?key=<key>&id=<id>
Body: product_name=<username>&store=<name of the shop that this product is in>&price=<normal price of the product>&cost=<cost>
- parameter "key" is the user key. 
- parameter "id" is the id of the product to update. Administrator may update any product, normal users can only update 
products from their own shops
- argument "product_name", "store", "price", "cost" may not need to be all present, only the present ones will be 
used to update the associated attribute
    - argument "store" must be a store that the user owns, unless the user is the administrator 
  
The returned json object would contain the attributes:
- updated_product: product name
- id: product id
- store: shop name of the shop that this product is in
- price: product normal price
- cost: product cost
  
#####DELETE (delete)
http://127.0.0.1:5000/api/v1/products?key=<key>&id=<id>
- parameter "key" is the user key
- parameter "id" is the id of the product to delete. Administrator may delete any products, normal users can only delete
 products from their own shop(s)
  
The returned json object would contain the attributes:
- deleted_product: product name
- id: product id
- store: shop name of the shop that this product is in
- price: product normal price
- cost: product cost 
  
  

###Orders:
#####GET (read)
http://127.0.0.1:5000/api/v1/orders?key=<key>&id=<id>&shop_id=<shop_id>&list=<true>
- parameter "key" is the user key
- parameter "id" specifies which order's information to get. Administrator may use any id, normal user can only use id of
orders from shops that he/she own
- parameter "shop_id" specifies which shop's orders' information to get. Administrator may use any id, normal user can only use the id of
shops that he/she own
- set parameter "list" to true to obtain a list of order. Administrator would get all order, normal user would only get 
order from shops that he/she own

If only one order's information is requested, would return a jason object that contains these attributes:
- id: order id
- store: shop name of the store which has this order 
- cost: cost of this product (cost in the sense that price-cost=income)
- line_items: a list of the ids of line items from this bill (order)
- total_price: total price of the items on this order, derived from the selling price of each line item
- total_cost: total cost of the items on this order, derived from the cost of the product type orf each line item
- total_income: total income from this order, derived from total price and total cost
    
If multiple orders' information is requested, the returned json would be:
- orders: a list of order object, each would have the above described attributes 

#####POST (create)
http://127.0.0.1:5000/api/v1/orders?key=<key>
Body: store=<name of the shop that this order is in>
- parameter "key" is the user key. 
- argument "store" must  be present (what it does is self-explanatory)
    - the store must be owned by the user, unless the user is the administrator

The returned json object would contain the attributes:
- created_order: order id
- store: shop name of the shop that has this order


#####PUT (update)
http://127.0.0.1:5000/api/v1/orders?key=<key>&id=<id>
Body: store=<name of the shop that this product is in>
- parameter "key" is the user key. 
- parameter "id" is the id of the order to update. Administrator may update any order, normal users can only update 
orders from their own shops
- argument "store" may not need to be present but if it is not present, this request would be doing nothing
    - argument "store" must be a store that the user owns, unless the user is the administrator 
  
The returned json object would contain the attributes:
- updated_order: order id
- store: shop name of the shop that has this order
  
#####DELETE (delete)
http://127.0.0.1:5000/api/v1/orders?key=<key>&id=<id>
- parameter "key" is the user key
- parameter "id" is the id of the order to delete. Administrator may delete any order, normal users can only delete
 orders from their own shop(s)
  
The returned json object would contain the attributes:
- deleted_order: order id
- store: shop name of the shop that has this order
  
  
###Line_Items:
#####GET (read)
http://127.0.0.1:5000/api/v1/line_items?key=<key>&id=<id>&product_id=<product_id>&order_id=<order_id>&shop_id=<shop_id>&list=<true>
- parameter "key" is the user key
- parameter "id" specifies which order's information to get. Administrator may use any id, normal user can only use id of
line items from shops that he/she own
- parameter "product_id" specifies which product's line items' information to get. Administrator may use any id, normal user can only use the id of
products from shops that he/she own
- parameter "order_id" specifies which order's line items' information to get. Administrator may use any id, normal user can only use the id of
orders from shops that he/she own
- parameter "shop_id" specifies which shop's line items' information to get. Administrator may use any id, normal user can only use the id of
shops that he/she own
- set parameter "list" to true to obtain a list of line items. Administrator would get all line items, normal user would only get 
line items from shops that he/she own

If only one line item's information is requested, would return a jason object that contains these attributes:
- id: order id
- product: product name of the type of product that this line item belongs to
- order: order id of the order that this line order belongs to
- unit_price: individual selling price of the type of product in this line item. Unit price could be different from the
general price of the product
- quantity: quantity of the type of product in this line item
    - The total price of a line item would be unit_price * quantity --> total price of a product/order is the sum of price
    of each line item from this product/order
    
If multiple line items' information is requested, the returned json would be:
- line_items: a list of item object, each would have the above described attributes  

#####POST (create)
http://127.0.0.1:5000/api/v1/line_items?key=<key>
Body: type=<name of the type of product that this line item is of>&order=<id of the order that this line item is from>
&price=<unit price of the line item>&quantity<quantity of the line item>
- parameter "key" is the user key. 
- argument "type", "order", "price", "quantity" must all be present (what they do is self-explanatory)
    - argument "type" and "order" must be products & orders from the shops that the user own, unless the user is the
    administrator  
  
The returned json object would contain the attributes:
- created_line_item: item id
- product: product name of the type of product that this line item belongs to
- order: order id of the order that this line order belongs to
- unit_price: individual selling price of the type of product in this line item.
- quantity: quantity of the type of product in this line item


#####PUT (update)
http://127.0.0.1:5000/api/v1/line_items?key=<key>&id=<id>
Body: type=<name of the type of product that this line item is of>&order=<id of the order that this line item is from>
&price=<unit price of the line item>&quantity<quantity of the line item>
- parameter "key" is the user key. 
- parameter "id" is the id of the line item to update. Administrator may update any item, normal users can only update 
items from their own shops
- argument "type", "order", "price", "quantity" may not need to be all present (only the presented ones will be used to update)
    - argument "type" and "order" must be products & orders from the shops that the user own, unless the user is the administrator 
  
The returned json object would contain the attributes:
- updated_line_item: item id
- product: product name of the type of product that this line item belongs to
- order: order id of the order that this line order belongs to
- unit_price: individual selling price of the type of product in this line item.
- quantity: quantity of the type of product in this line item
  
#####DELETE (delete)
http://127.0.0.1:5000/api/v1/line_items?key=<key>&id=<id>
- parameter "key" is the user key
- parameter "id" is the id of the line item to delete. Administrator may delete any line item, normal users can only delete
 line items from their own shop(s)
  
The returned json object would contain the attributes:
- deleted_line_item: item id
- product: product name of the type of product that this line item belongs to
- order: order id of the order that this line order belongs to
- unit_price: individual selling price of the type of product in this line item.
- quantity: quantity of the type of product in this line item  
  
  
  
#### Framework and Library:
- python flask
- python flask-sqlalchemy
- python flask-restful



#### Author:
- Qinyang Bao


