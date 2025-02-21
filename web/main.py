import flask
from flask import render_template, redirect, url_for, flash, request
import models 
import forms
import acl
from flask import Blueprint
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
import base64

module = Blueprint("templates", __name__)

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

def b64encode(data):
    return base64.b64encode(data).decode('utf-8')

# สร้าง LoginManager
login_manager = LoginManager()
login_manager.init_app(app)  # ตั้งค่า LoginManager
login_manager.login_view = "login"  # ตั้งค่าหน้าเว็บที่ต้องการให้ผู้ใช้ไปเมื่อยังไม่ได้ล็อกอิน
acl.init_acl(app)  # ใช้ฟังก์ชัน init_acl จาก acl.py
models.init_app(app)
app.jinja_env.filters['b64encode'] = b64encode
# ตั้งค่าฟังก์ชันสำหรับโหลดผู้ใช้
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

@app.route("/")
def index():
    latest_year = models.db.session.query(models.Cost_of_Living.year).order_by(models.Cost_of_Living.year.desc()).first()[0]
    previous_year = latest_year - 1

    latest_cost = models.Cost_of_Living.query.filter_by(province_name="Thailand", year=latest_year).first()
    previous_cost = models.Cost_of_Living.query.filter_by(province_name="Thailand", year=previous_year).first()
    province = models.Province.query.filter_by(name="Thailand").first()

    cost_comparison = {
        "latest": latest_cost,
        "previous": previous_cost,
        "food_diff": ((latest_cost.food - previous_cost.food) / previous_cost.food) * 100,
        "housing_diff": ((latest_cost.housing - previous_cost.housing) / previous_cost.housing) * 100,
        "energy_diff": ((latest_cost.energy - previous_cost.energy) / previous_cost.energy) * 100,
        "transportation_diff": ((latest_cost.transportation - previous_cost.transportation) / previous_cost.transportation) * 100,
        "entertainment_diff": ((latest_cost.entertainment - previous_cost.entertainment) / previous_cost.entertainment) * 100,
        "total_cost_diff": ((latest_cost.total_cost - previous_cost.total_cost) / previous_cost.total_cost) * 100,
    }

    return render_template("index.html", cost_comparison=cost_comparison, province=province, latest_year=latest_year, previous_year=previous_year)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()  # สร้างฟอร์มล็อกอิน
    if form.validate_on_submit():  # ตรวจสอบการส่งฟอร์ม
        user = models.User.query.filter_by(username=form.username.data).first()  # ค้นหาผู้ใช้
        if user and user.authenticate(form.password.data):  # ตรวจสอบรหัสผ่าน
            login_user(user)  # ล็อกอินผู้ใช้
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("index"))
        flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)  # แสดงฟอร์ม

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        existing_user = models.User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("บัญชีนี้มีอยู่แล้ว กรุณาใช้ชื่อผู้ใช้อื่น", "danger")
            return render_template("register.html", form=form)
        
        user = models.User()
        form.populate_obj(user)
        role = models.Role.query.filter_by(name="user").first()
        if not role:
            role = models.Role(name="user")
            models.db.session.add(role)
        user.roles.append(role)
        user.password_hash = form.password.data
        models.db.session.add(user)
        models.db.session.commit()
        flash("ลงทะเบียนสำเร็จ! กรุณาเข้าสู่ระบบ", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/create_province", methods=["GET", "POST"])
@login_required
def create_province():
    form = forms.Province_Form()
    
    if form.validate_on_submit():
        existing_province = models.Province.query.filter_by(name=form.name.data).first()
        if existing_province:
            flash("Province already exists!", "danger")
            return render_template("create_province.html", form=form)
        
        try:
            # อ่านข้อมูลไฟล์
            image_data = None
            if form.image_file.data:
                image_data = form.image_file.data.read()
            
            province = models.Province(
                name=form.name.data,
                region=form.region.data,
                image_file=image_data  # บันทึกข้อมูลไฟล์
            )
            models.db.session.add(province)
            models.db.session.commit()
            flash("Province added successfully", "success")
            return redirect(url_for("index"))
        except Exception as e:
            models.db.session.rollback()
            flash("Failed to add province. Error: " + str(e), "danger")
    
    return render_template("create_province.html", form=form)

@app.route("/create_cost_of_living", methods=["GET", "POST"])
@login_required
def create_cost_of_living():
    form = forms.Cost_of_Living_Form()
    form.province_name.choices = [(p.name, p.name) for p in models.Province.query.all()]
    form.year.choices = [(year, year) for year in range(2000, 2026)]  # กำหนดตัวเลือกปีตั้งแต่ 2000 ถึง 2025

    if form.validate_on_submit():
        existing_cost = models.Cost_of_Living.query.filter_by(
            province_name=form.province_name.data,
            year=form.year.data
        ).first()
        
        if existing_cost:
            flash("Cost of living for this province and year already exists!", "danger")
            return render_template("create_cost_of_living.html", form=form)

        try:
            total_cost = form.food.data + form.housing.data + form.energy.data + form.transportation.data + form.entertainment.data  # คำนวณค่า total_cost
            cost = models.Cost_of_Living(
                province_name=form.province_name.data,
                year=form.year.data,
                food=form.food.data,
                housing=form.housing.data,
                energy=form.energy.data,
                transportation=form.transportation.data,
                entertainment=form.entertainment.data,
                total_cost=total_cost  # บันทึกค่า total_cost
            )
            models.db.session.add(cost)
            models.db.session.commit()
            flash("Cost of living added successfully", "success")
            return redirect(url_for("index"))
        except Exception as e:
            models.db.session.rollback()
            flash("Failed to add cost of living. Error: " + str(e), "danger")

    return render_template("create_cost_of_living.html", form=form)

@app.route("/compare_cost", methods=["GET", "POST"])
@login_required
def compare_cost():
    provinces = models.Province.query.all()
    years = range(2020, 2024)
    cost1 = None
    cost2 = None
    province1 = None
    province2 = None
    year1 = None
    year2 = None

    if request.method == "POST":
        province1_name = request.form.get("province1")
        province2_name = request.form.get("province2")
        year1 = request.form.get("year1")
        year2 = request.form.get("year2")

        if province1_name and province2_name and year1 and year2:
            province1 = models.Province.query.filter_by(name=province1_name).first()
            province2 = models.Province.query.filter_by(name=province2_name).first()
            cost1 = models.Cost_of_Living.query.filter_by(province_name=province1_name, year=year1).first()
            cost2 = models.Cost_of_Living.query.filter_by(province_name=province2_name, year=year2).first()

    return render_template("compare_cost.html", provinces=provinces, years=years, cost1=cost1, cost2=cost2, province1=province1, province2=province2, year1=year1, year2=year2)

if __name__ == "__main__":
    app.run(debug=True)