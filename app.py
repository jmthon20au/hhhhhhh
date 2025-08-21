import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='.', static_url_path='')

# تهيئة CORS للسماح بالطلبات من أي مصدر (*).
# في بيئة الإنتاج، يفضل تحديد أصول محددة (domains) بدلاً من '*' لأسباب أمنية.
# مثال: CORS(app, resources={r"/*": {"origins": ["https://your-frontend-domain.com", "http://127.0.0.1:5000"]}})
CORS(app)

DATA_FILE = 'data.json'

# دالة لقراءة البيانات من ملف JSON
def read_data():
    if not os.path.exists(DATA_FILE):
        # إذا كان الملف غير موجود، أنشئ هيكلاً فارغاً للمستخدمين والمنتجات
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"users": [], "products": []}, f, indent=2, ensure_ascii=False)
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # التعامل مع ملف JSON فارغ أو تالف، وإرجاع هيكل افتراضي
        print(f"Error reading {DATA_FILE}: File is empty or corrupted. Initializing with empty data.")
        return {"users": [], "products": []}

# دالة لكتابة البيانات إلى ملف JSON
def write_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# مسار الصفحة الرئيسية (صفحة تسجيل الدخول)
@app.route('/')
def serve_login_page():
    return send_from_directory('.', 'index.html')

# مسار لوحة التحكم
@app.route('/dashboard.html')
def serve_dashboard_page():
    return send_from_directory('.', 'dashboard.html')

# نقطة نهاية لتسجيل الدخول (POST request)
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

# نقطة نهاية لجلب جميع المنتجات (GET request)
@app.route('/products', methods=['GET'])
def get_products():
    data = read_data()
    return jsonify(data.get('products', []))

# نقطة نهاية لجلب منتج معين بواسطة تسلسله (GET request)
@app.route('/product/<product_id>', methods=['GET'])
def get_product(product_id):
    data = read_data()
    products = data.get('products', [])
    # البحث عن المنتج باستخدام تسلسل المنتج
    product = next((p for p in products if p['productId'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({"message": "المنتج غير موجود."}), 404

# نقطة نهاية لتحديث كمية منتج (إضافة أو خصم) (POST request)
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
                product['quantity'] = 0 # منع الكمية السالبة
            product_found = True
            break
    
    if product_found:
        write_data(data)
        return jsonify({"success": True, "message": "تم تحديث الكمية بنجاح!"})
    return jsonify({"success": False, "message": "المنتج غير موجود."}), 404

# نقطة نهاية لإضافة منتج جديد (POST request)
@app.route('/add_product', methods=['POST'])
def add_product():
    new_product = request.json
    company_name = new_product.get('companyName')
    product_id = new_product.get('productId')
    quantity = new_product.get('quantity')
    image_url = new_product.get('imageUrl')

    # التحقق من وجود جميع الحقول المطلوبة
    if not all([company_name, product_id, quantity is not None, image_url]):
        return jsonify({"success": False, "message": "يرجى إدخال جميع الحقول المطلوبة."}), 400

    data = read_data()
    products = data.get('products', [])

    # التحقق مما إذا كان المنتج موجوداً بالفعل (تسلسل فريد)
    if any(p['productId'] == product_id for p in products):
        return jsonify({"success": False, "message": "منتج بهذا التسلسل موجود بالفعل!"}), 409

    products.append({
        "companyName": company_name,
        "productId": product_id,
        "quantity": quantity,
        "imageUrl": image_url
    })
    data['products'] = products
    write_data(data)
    return jsonify({"success": True, "message": "تمت إضافة المنتج بنجاح!"})

if __name__ == '__main__':
    # تشغيل الخادم على المنفذ 5000 في وضع التطوير
    app.run(debug=True, port=5000)
