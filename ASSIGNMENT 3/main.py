from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()
# database
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    
    # {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    # {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    # {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]
feedback = []
orders = []
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)
class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)
class NewProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

# home
@app.get("/")
def home():
    return {"message": "FastAPI Store API Running"}

# Q1: products
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

# A3 - Q1: Add New Products Using POST
@app.post("/products")
def add_product(new_product: NewProduct, response: Response):
    # check duplicate product name
    existing_names = [p["name"].lower() for p in products]
    if new_product.name.lower() in existing_names:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Product with this name already exists"}
    # generate next id
    next_id = max(p["id"] for p in products) + 1
    product = {
        "id": next_id,
        "name": new_product.name,
        "price": new_product.price,
        "category": new_product.category,
        "in_stock": new_product.in_stock
    }
    products.append(product)
    response.status_code = status.HTTP_201_CREATED
    return {
        "message": "Product added",
        "product": product
    }

#Q2: products/category/{category}
@app.get("/products/category/{category}")
def get_products_by_category(category: str):
    result = [p for p in products if p["category"].lower() == category.lower()]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category, "products": result}

#Q3: instock
@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"] == True]
    return {
        "in_stock_products": available,
        "count": len(available)
    }

#Q4: store/summary
@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    categories = list(set([p["category"] for p in products]))
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }

#Q5: products/search/{keyword}
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]
    if not results:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "results": results,
        "total_matches": len(results)
    }

# Bonus- products/deals  
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }

# A2 - Q1 - Filter products
@app.get("/products/filter")
def filter_products(
    category: str = Query(None),
    max_price: int = Query(None),
    min_price: int = Query(None, description="Minimum price")
):
    result = products
    # filter by category
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    # filter by max price
    if max_price:
        result = [p for p in result if p["price"] <= max_price]
    # NEW filter (this is the task requirement)
    if min_price:
        result = [p for p in result if p["price"] >= min_price]
    return {
        "filtered_products": result,
        "count": len(result)
    }

# A3 - Q5 - GET /products/audit-Inventory Summary
@app.get("/products/audit")
def products_audit():
    in_stock_products = [p for p in products if p["in_stock"]]
    out_of_stock_products = [p for p in products if not p["in_stock"]]
    total_stock_value = sum(p["price"] * 10 for p in in_stock_products)
    most_expensive = max(products, key=lambda p: p["price"])
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_products),
        "out_of_stock_names": [p["name"] for p in out_of_stock_products],
        "total_stock_value": total_stock_value,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        }
    }

# A3 - Bonus - Category-Wide Discount
@app.put("/products/discount")
def apply_discount(
    category: str = Query(..., description="Category to discount"),
    discount_percent: int = Query(..., ge=1, le=99, description="Discount percent")
):
    updated_products = []

    for p in products:
        if p["category"].lower() == category.lower():

            new_price = int(p["price"] * (1 - discount_percent / 100))
            p["price"] = new_price

            updated_products.append({
                "name": p["name"],
                "new_price": new_price
            })
    if not updated_products:
        return {"message": f"No products found in category: {category}"}
    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated_products),
        "products": updated_products
    }

# A2 - Q2 - Get product price by ID
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"],
                "in_stock":product["in_stock"]
            }
    return {"error": "Product not found"}

# A3 - Q2 - Restock Using PUT
@app.put("/products/{product_id}")
def update_product(product_id: int, in_stock: bool = Query(None), price: int = Query(None)):
    for product in products:
        if product["id"] == product_id:
            if in_stock is not None:
                product["in_stock"] = in_stock
            if price is not None:
                product["price"] = price
            return {"message": "Product updated", "product": product}
    return {"error": "Product not found"}

# A2 - Q3 - Customer Feedback
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }

#  A2 - Q4 - Product summary dashboard
@app.get("/products/summary") 
def product_summary():
    in_stock   = [p for p in products if p["in_stock"]]
    out_stock  = [p for p in products if not p["in_stock"]]
    expensive  = max(products, key=lambda p: p["price"])
    cheapest   = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }

#  A2 - Q5 -  Bulk Order
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })
    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

#  A2 - BONUS - Order Status Tracker
@app.post("/orders")
def place_order(product_id: int, quantity: int):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return {"error": "Product not found"}
    order = {
        "order_id": len(orders) + 1,
        "product": product["name"],
        "quantity": quantity,
        "status": "pending"
    }
    orders.append(order)
    return {"message": "Order placed", "order": order}

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }
    return {"error": "Order not found"}

# A3 - Q3 : Delete a Product
@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": f"Product '{product['name']}' deleted"}
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": "Product not found"}
