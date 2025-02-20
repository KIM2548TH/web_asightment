import flask
from flask import render_template, redirect, url_for, flash
import models 
import forms
import acl
from flask import Blueprint
from flask_login import LoginManager, login_required, login_user, logout_user

module = Blueprint("templates", __name__)

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

# สร้าง LoginManager
login_manager = LoginManager()
login_manager.init_app(app)  # ตั้งค่า LoginManager
models.init_app(app)

# ตั้งค่าฟังก์ชันสำหรับโหลดผู้ใช้
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))


@app.route("/")
def index():
    notes = models.Note.query.order_by(models.Note.title).all()
    return render_template("index.html", notes=notes)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()  # สร้างฟอร์มล็อกอิน
    if form.validate_on_submit():  # ตรวจสอบการส่งฟอร์ม
        user = models.User.query.filter_by(username=form.username.data).first()  # ค้นหาผู้ใช้
        if user and user.authenticate(form.password.data):  # ตรวจสอบรหัสผ่าน
            login_user(user)  # ล็อกอินผู้ใช้
            return redirect(url_for("index"))
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
            if form.image_url.data:
                image_data = form.image_url.data.read()
            
            province = models.Province(
                name=form.name.data,
                region=form.region.data,
                image_url=form.image_url.data.filename,  # บันทึกชื่อไฟล์
                image_data=image_data  # บันทึกข้อมูลไฟล์
            )
            models.db.session.add(province)
            models.db.session.commit()
            flash("Province added successfully", "success")
            return redirect(url_for("index"))
        except Exception as e:
            models.db.session.rollback()
            flash("Failed to add province. Error: " + str(e), "danger")
    
    return render_template("create_province.html", form=form)

@login_required
@app.route("/create_cost_of_living", methods=["GET", "POST"])
def create_cost_of_living():
    form = forms.Cost_of_Living_Form()
    form.province_name.choices = [(p.name, p.name) for p in models.Province.query.all()]

    if form.validate_on_submit():
        existing_cost = models.Cost_of_Living.query.filter_by(
            province_name=form.province_name.data,
            year=form.year.data
        ).first()
        
        if existing_cost:
            flash("Cost of living for this province and year already exists!", "danger")
            return render_template("create_cost_of_living.html", form=form)

        try:
            cost = models.Cost_of_Living(
                province_name=form.province_name.data,
                year=form.year.data,
                food=form.food.data,
                housing=form.housing.data,
                energy=form.energy.data
            )
            models.db.session.add(cost)
            models.db.session.commit()
            flash("Cost of living added successfully", "success")
            return redirect(url_for("index"))
        except Exception as e:
            models.db.session.rollback()
            flash("Failed to add cost of living. Error: " + str(e), "danger")

    return render_template("create_cost_of_living.html", form=form)

if __name__ == "__main__":
    app.run(debug=True)
