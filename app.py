import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app) # تمكين CORS للسماح لطلبات JavaScript من المتصفح بالوصول إلى الخادم

DATA_FILE = 'data.json'

# دالة لقراءة البيانات من ملف JSON
def read_data():
    if not os.path.exists(DATA_FILE):
        # إذا كان الملف غير موجود، أنشئ هيكلاً فارغاً
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"users": [], "products": []}, f, indent=2, ensure_ascii=False)
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # التعامل مع ملف JSON فارغ أو تالف
        return {"users": [], "products": []}

# دالة لكتابة البيانات إلى ملف JSON
def write_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/')
def serve_login_page():
    return send_from_directory('.', 'index.html')

@app.route('/dashboard.html')
def serve_dashboard_page():
    return send_from_directory('.', 'dashboard.html')

# نقطة نهاية لتسجيل الدخول
@app.route('/login', methods=['POST'])
def login():
    credentials = request.json
    username = credentials.get('username')
    password = credentials.get('password')
    data = read_data()
    users = data.get('users', [])
    for user in users:
        if user['username'] == username and user['password'] == password:
            return jsonify({"success": True, "message": "تم تسجيل الدخول بنجاح!"})
    return jsonify({"success": False, "message": "اسم المستخدم أو كلمة المرور غير صحيحة."}), 401

# نقطة نهاية لجلب جميع المنتجات
@app.route('/products', methods=['GET'])
def get_products():
    data = read_data()
    return jsonify(data.get('products', []))

# نقطة نهاية لجلب منتج معين بواسطة تسلسله
@app.route('/product/<product_id>', methods=['GET'])
def get_product(product_id):
    data = read_data()
    products = data.get('products', [])
    product = next((p for p in products if p['productId'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({"message": "المنتج غير موجود."}), 404

# نقطة نهاية لإضافة/خصم كمية من منتج
@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    update_data = request.json
    product_id = update_data.get('productId')
    quantity_change = update_data.get('quantityChange') # يمكن أن تكون موجبة للإضافة أو سالبة للخصم

    data = read_data()
    products = data.get('products', [])
    
    product_found = False
    for product in products:
        if product['productId'] == product_id:
            product['quantity'] += quantity_change
            if product['quantity'] < 0:
                product['quantity'] = 0 # لا تسمح بكمية سالبة
            product_found = True
            break
    
    if product_found:
        write_data(data)
        return jsonify({"success": True, "message": "تم تحديث الكمية بنجاح."})
    return jsonify({"success": False, "message": "المنتج غير موجود."}), 404

# نقطة نهاية لإضافة منتج جديد
@app.route('/add_product', methods=['POST'])
def add_product():
    new_product = request.json
    company_name = new_product.get('companyName')
    product_id = new_product.get('productId')
    quantity = new_product.get('quantity')
    image_url = new_product.get('imageUrl')

    if not all([company_name, product_id, quantity, image_url]):
        return jsonify({"success": False, "message": "يرجى إدخال جميع الحقول المطلوبة."}), 400

    data = read_data()
    products = data.get('products', [])

    # التحقق مما إذا كان المنتج موجوداً بالفعل
    if any(p['productId'] == product_id for p in products):
        return jsonify({"success": False, "message": "هذا المنتج موجود بالفعل."}), 409

    products.append({
        "companyName": company_name,
        "productId": product_id,
        "quantity": quantity,
        "imageUrl": image_url
    })
    data['products'] = products
    write_data(data)
    return jsonify({"success": True, "message": "تم إضافة المنتج بنجاح."})

if __name__ == '__main__':
    app.run(debug=True, port=5000) # تشغيل الخادم على المنفذ 5000
