import flask
from flask import render_template, redirect, url_for, flash, request
import models 
import forms
import acl
from flask import Blueprint
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
import base64
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

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
    # ดึงค่าที่มีค่ามากที่สุดและค่าที่มีค่ามากที่สุดลำดับสอง
    top_two_years = models.db.session.query(models.Cost_of_Living.year).order_by(models.Cost_of_Living.total_cost.desc()).limit(2).all()
    if len(top_two_years) < 2:
        flash("Not enough data to compare.", "danger")
        return render_template("index.html", cost_comparison=None, province=None, latest_year=None, previous_year=None)

    latest_year = top_two_years[0][0]
    previous_year = top_two_years[1][0]

    latest_cost = models.Cost_of_Living.query.filter_by(province_name="Thailand", year=latest_year).first()
    previous_cost = models.Cost_of_Living.query.filter_by(province_name="Thailand", year=previous_year).first()
    province = models.Province.query.filter_by(name="Thailand").first()

    cost_comparison = {
        "latest": latest_cost,
        "previous": previous_cost,
        "food_diff": latest_cost.food - previous_cost.food,
        "housing_diff": latest_cost.housing - previous_cost.housing,
        "energy_diff": latest_cost.energy - previous_cost.energy,
        "transportation_diff": latest_cost.transportation - previous_cost.transportation,
        "entertainment_diff": latest_cost.entertainment - previous_cost.entertainment,
        "total_cost_diff": latest_cost.total_cost - previous_cost.total_cost,
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

@app.route("/view_compare_cost", methods=["GET", "POST"])
@login_required
def view_compare_cost():
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

    return render_template("view_compare_cost.html", provinces=provinces, years=years, cost1=cost1, cost2=cost2, province1=province1, province2=province2, year1=year1, year2=year2)

@app.route("/view_province", methods=["GET", "POST"])
@login_required
def view_province():
    provinces = models.Province.query.all()
    years = models.db.session.query(models.Cost_of_Living.year).distinct().order_by(models.Cost_of_Living.year.desc()).all()
    years = [year[0] for year in years]

    if request.method == "POST":
        province_name = request.form.get("province")
        year = request.form.get("year")

        if not province_name or not year:
            flash("Please select both province and year.", "danger")
            return redirect(url_for("view_province"))

        province = models.Province.query.filter_by(name=province_name).first()
        cost = models.Cost_of_Living.query.filter_by(province_name=province_name, year=year).first()
        previous_year = int(year) - 1
        previous_cost = models.Cost_of_Living.query.filter_by(province_name=province_name, year=previous_year).first()

        if not cost:
            flash("No data available for the selected province and year.", "danger")
            return redirect(url_for("view_province"))

        if not previous_cost:
            flash("No data available for the previous year.", "danger")
            return redirect(url_for("view_province"))

        return render_template("view_province.html", province=province, year=year, previous_year=previous_year, cost=cost, previous_cost=previous_cost, provinces=provinces, years=years)

    return render_template("view_province.html", provinces=provinces, years=years, cost=None)

@app.route("/view_province/show_graphs", methods=["POST"])
@login_required
def show_graphs():
    province_name = request.form.get("province_name")
    if not province_name:
        flash("Province name is required.", "danger")
        return redirect(url_for("view_province"))

    costs = models.Cost_of_Living.query.filter_by(province_name=province_name).all()
    if not costs:
        flash("No cost of living data available for the selected province.", "danger")
        return redirect(url_for("view_province"))

    # Prepare data for the graphs
    data = {
        "Year": [cost.year for cost in costs],
        "Food": [cost.food for cost in costs],
        "Housing": [cost.housing for cost in costs],
        "Energy": [cost.energy for cost in costs],
        "Transportation": [cost.transportation for cost in costs],
        "Entertainment": [cost.entertainment for cost in costs],
        "Total Cost": [cost.total_cost for cost in costs],
    }
    df = pd.DataFrame(data)

    # Calculate percentage increase for the latest year
    latest_year = df["Year"].max()
    previous_year = latest_year - 1
    latest_total_cost = df[df["Year"] == latest_year]["Total Cost"].values[0]
    previous_total_cost = df[df["Year"] == previous_year]["Total Cost"].values[0]
    percentage_increase = ((latest_total_cost - previous_total_cost) / previous_total_cost) * 100

    # Predict the trend for the next year using linear regression
    x = np.array(df["Year"]).reshape(-1, 1)
    y = np.array(df["Total Cost"]).reshape(-1, 1)
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(x, y)
    next_year = latest_year + 1
    predicted_cost = model.predict([[next_year]])[0][0]
    trend_percentage = ((predicted_cost - latest_total_cost) / latest_total_cost) * 100

    # Calculate trends for each category
    trends = {}
    for column in df.columns[1:]:
        y = np.array(df[column]).reshape(-1, 1)
        model.fit(x, y)
        predicted_value = model.predict([[next_year]])[0][0]
        latest_value = df[df["Year"] == latest_year][column].values[0]
        trend_percentage = ((predicted_value - latest_value) / latest_value) * 100
        trends[column] = trend_percentage

    # Create bar chart
    bar_fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, column in enumerate(df.columns[1:]):
        bar_fig.add_trace(go.Bar(x=df["Year"], y=df[column], name=column, marker_color=colors[i % len(colors)]))

    bar_fig.update_layout(
        title=f"Cost of Living in {province_name} Over Years (Bar Chart)",
        xaxis_title="Year",
        yaxis_title="Cost",
        barmode='group',
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )

    bar_chart = bar_fig.to_html(full_html=False)

    # Create line chart
    line_fig = go.Figure()
    for i, column in enumerate(df.columns[1:]):
        line_fig.add_trace(go.Scatter(x=df["Year"], y=df[column], mode='lines+markers', name=column, line=dict(color=colors[i % len(colors)])))

    line_fig.update_layout(
        title=f"Cost of Living in {province_name} Over Years (Line Chart)",
        xaxis_title="Year",
        yaxis_title="Cost",
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )

    line_chart = line_fig.to_html(full_html=False)

    # Create pie chart for the latest year
    pie_data = df[df["Year"] == latest_year].iloc[0][1:].to_dict()
    pie_fig = px.pie(names=pie_data.keys(), values=pie_data.values(), title=f"Cost Distribution for {latest_year}", color_discrete_sequence=colors)
    pie_fig.update_layout(
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )
    pie_chart = pie_fig.to_html(full_html=False)

    return render_template("show_graphs.html", bar_chart=bar_chart, line_chart=line_chart, pie_chart=pie_chart, province_name=province_name, percentage_increase=percentage_increase, trends=trends, trend_percentage=trend_percentage)

@app.route("/compare_cost/compare_graphs", methods=["POST"])
@login_required
def compare_graphs():
    province_name1 = request.form.get("province_name1")
    province_name2 = request.form.get("province_name2")
    if not province_name1 or not province_name2:
        flash("Both province names are required.", "danger")
        return redirect(url_for("compare_cost"))

    costs1 = models.Cost_of_Living.query.filter_by(province_name=province_name1).all()
    costs2 = models.Cost_of_Living.query.filter_by(province_name=province_name2).all()
    if not costs1 or not costs2:
        flash("No cost of living data available for the selected provinces.", "danger")
        return redirect(url_for("compare_cost"))

    # Prepare data for the graphs
    data1 = {
        "Year": [cost.year for cost in costs1],
        "Food": [cost.food for cost in costs1],
        "Housing": [cost.housing for cost in costs1],
        "Energy": [cost.energy for cost in costs1],
        "Transportation": [cost.transportation for cost in costs1],
        "Entertainment": [cost.entertainment for cost in costs1],
        "Total Cost": [cost.total_cost for cost in costs1],
    }
    df1 = pd.DataFrame(data1)

    data2 = {
        "Year": [cost.year for cost in costs2],
        "Food": [cost.food for cost in costs2],
        "Housing": [cost.housing for cost in costs2],
        "Energy": [cost.energy for cost in costs2],
        "Transportation": [cost.transportation for cost in costs2],
        "Entertainment": [cost.entertainment for cost in costs2],
        "Total Cost": [cost.total_cost for cost in costs2],
    }
    df2 = pd.DataFrame(data2)

    # Calculate trends for each category
    trends1 = {}
    trends2 = {}
    for column in df1.columns[1:]:
        x1 = np.array(df1["Year"]).reshape(-1, 1)
        y1 = np.array(df1[column]).reshape(-1, 1)
        model1 = LinearRegression()
        model1.fit(x1, y1)
        next_year1 = df1["Year"].max() + 1
        predicted_value1 = model1.predict([[next_year1]])[0][0]
        latest_value1 = df1[df1["Year"] == df1["Year"].max()][column].values[0]
        trend_percentage1 = ((predicted_value1 - latest_value1) / latest_value1) * 100
        trends1[column] = trend_percentage1

        x2 = np.array(df2["Year"]).reshape(-1, 1)
        y2 = np.array(df2[column]).reshape(-1, 1)
        model2 = LinearRegression()
        model2.fit(x2, y2)
        next_year2 = df2["Year"].max() + 1
        predicted_value2 = model2.predict([[next_year2]])[0][0]
        latest_value2 = df2[df2["Year"] == df2["Year"].max()][column].values[0]
        trend_percentage2 = ((predicted_value2 - latest_value2) / latest_value2) * 100
        trends2[column] = trend_percentage2

    # Create bar chart
    bar_fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e']
    for i, column in enumerate(df1.columns[1:]):
        bar_fig.add_trace(go.Bar(x=df1["Year"], y=df1[column], name=f"{province_name1} - {column}", marker_color=colors[0]))
        bar_fig.add_trace(go.Bar(x=df2["Year"], y=df2[column], name=f"{province_name2} - {column}", marker_color=colors[1]))

    bar_fig.update_layout(
        title=f"Cost of Living Comparison: {province_name1} vs {province_name2} (Bar Chart)",
        xaxis_title="Year",
        yaxis_title="Cost",
        barmode='group',
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )

    bar_chart = bar_fig.to_html(full_html=False)

    # Create line chart
    line_fig = go.Figure()
    for i, column in enumerate(df1.columns[1:]):
        line_fig.add_trace(go.Scatter(x=df1["Year"], y=df1[column], mode='lines+markers', name=f"{province_name1} - {column}", line=dict(color=colors[0])))
        line_fig.add_trace(go.Scatter(x=df2["Year"], y=df2[column], mode='lines+markers', name=f"{province_name2} - {column}", line=dict(color=colors[1])))

    line_fig.update_layout(
        title=f"Cost of Living Comparison: {province_name1} vs {province_name2} (Line Chart)",
        xaxis_title="Year",
        yaxis_title="Cost",
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )

    line_chart = line_fig.to_html(full_html=False)

    # Create pie chart for the latest year
    latest_year1 = df1["Year"].max()
    latest_year2 = df2["Year"].max()
    pie_data1 = df1[df1["Year"] == latest_year1].iloc[0][1:].to_dict()
    pie_data2 = df2[df2["Year"] == latest_year2].iloc[0][1:].to_dict()
    pie_fig1 = px.pie(names=pie_data1.keys(), values=pie_data1.values(), title=f"Cost Distribution for {province_name1} ({latest_year1})", color_discrete_sequence=[colors[0]])
    pie_fig2 = px.pie(names=pie_data2.keys(), values=pie_data2.values(), title=f"Cost Distribution for {province_name2} ({latest_year2})", color_discrete_sequence=[colors[1]])

    pie_fig1.update_layout(
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )
    pie_fig2.update_layout(
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#333333')
    )

    pie_chart1 = pie_fig1.to_html(full_html=False)
    pie_chart2 = pie_fig2.to_html(full_html=False)

    return render_template("compare_graphs.html", bar_chart=bar_chart, line_chart=line_chart, pie_chart1=pie_chart1, pie_chart2=pie_chart2, province_name1=province_name1, province_name2=province_name2, trends1=trends1, trends2=trends2)

if __name__ == "__main__":
    app.run(debug=True)