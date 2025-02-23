from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import models
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

def read_image(file_path):
    with open(file_path, "rb") as file:
        return file.read()
class Province(db.Model):
    __tablename__ = "provinces"
    name = db.Column(db.String(100), primary_key=True, unique=True, nullable=False)
    region = db.Column(db.String(50), nullable=False)
    image_file = db.Column(db.LargeBinary, nullable=True)
    cost_of_living = db.relationship("Cost_of_Living", back_populates="province")
    created_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Cost_of_Living(db.Model):
    __tablename__ = "cost_of_livings"
    id = db.Column(db.Integer, primary_key=True)
    province_name = db.Column(db.String(100), db.ForeignKey("provinces.name"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    food = db.Column(db.Integer, nullable=False)
    housing = db.Column(db.Integer, nullable=False)
    energy = db.Column(db.Integer, nullable=False)
    transportation = db.Column(db.Integer, nullable=False)
    entertainment = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Integer, nullable=False)
    province = db.relationship("Province", back_populates="cost_of_living")
    created_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

def add_data():
    data = [
        {
            "province_name": "Thailand",
            "region": "กลาง",
            "image_file": read_image("static/images/thailand.png"),
            "cost_of_living": [
                {"year": 2020, "food": 5000, "housing": 7500, "energy": 1500, "transportation": 2000, "entertainment": 2500, "total_cost": 18500},
                {"year": 2021, "food": 5150, "housing": 7725, "energy": 1545, "transportation": 2060, "entertainment": 2575, "total_cost": 19055},
                {"year": 2022, "food": 5304.5, "housing": 7956.75, "energy": 1591.35, "transportation": 2121.8, "entertainment": 2652.25, "total_cost": 19626.65},
                {"year": 2023, "food": 5463.64, "housing": 8195.45, "energy": 1639.09, "transportation": 2185.45, "entertainment": 2731.82, "total_cost": 20215.45},
                {"year": 2024, "food": 5627.55, "housing": 8441.32, "energy": 1688.26, "transportation": 2251.02, "entertainment": 2813.77, "total_cost": 20822.92}
            ]
        },
        {
            "province_name": "Chiang Mai",
            "region": "เหนือ",
            "image_file": read_image("static/images/ChiangMai.png"),
            "cost_of_living": [
                {"year": 2020, "food": 4000, "housing": 6000, "energy": 1000, "transportation": 1500, "entertainment": 2000, "total_cost": 14500},
                {"year": 2021, "food": 4120, "housing": 6180, "energy": 1030, "transportation": 1545, "entertainment": 2060, "total_cost": 14935},
                {"year": 2022, "food": 4243.6, "housing": 6365.4, "energy": 1060.9, "transportation": 1591.35, "entertainment": 2121.8, "total_cost": 15382.05},
                {"year": 2023, "food": 4368.91, "housing": 6556.36, "energy": 1092.73, "transportation": 1639.09, "entertainment": 2185.45, "total_cost": 15842.55},
                {"year": 2024, "food": 4496.98, "housing": 6753.05, "energy": 1125.51, "transportation": 1688.26, "entertainment": 2251.02, "total_cost": 16315.82}
            ]
        },
        {
            "province_name": "Khon Kaen",
            "region": "อีสาน",
            "image_file": read_image("static/images/KhonKaen.png"),
            "cost_of_living": [
                {"year": 2020, "food": 3500, "housing": 5000, "energy": 750, "transportation": 1250, "entertainment": 1500, "total_cost": 12000},
                {"year": 2021, "food": 3605, "housing": 5150, "energy": 772.5, "transportation": 1287.5, "entertainment": 1545, "total_cost": 12360},
                {"year": 2022, "food": 3713.15, "housing": 5304.5, "energy": 795.68, "transportation": 1326.13, "entertainment": 1591.35, "total_cost": 12730.81},
                {"year": 2023, "food": 3824.54, "housing": 5463.64, "energy": 819.55, "transportation": 1365.91, "entertainment": 1639.09, "total_cost": 13112.73},
                {"year": 2024, "food": 3939.28, "housing": 5627.55, "energy": 844.14, "transportation": 1406.89, "entertainment": 1688.26, "total_cost": 13505.12}
            ]
        },
        {
            "province_name": "Phuket",
            "region": "ใต้",
            "image_file": read_image("static/images/Phuket.png"),
            "cost_of_living": [
                {"year": 2020, "food": 4500, "housing": 7000, "energy": 1250, "transportation": 1750, "entertainment": 2250, "total_cost": 16750},
                {"year": 2021, "food": 4635, "housing": 7210, "energy": 1287.5, "transportation": 1802.5, "entertainment": 2317.5, "total_cost": 17252.5},
                {"year": 2022, "food": 4774.05, "housing": 7426.3, "energy": 1326.13, "transportation": 1856.58, "entertainment": 2386.03, "total_cost": 17769.09},
                {"year": 2023, "food": 4917.27, "housing": 7649.09, "energy": 1365.91, "transportation": 1912.27, "entertainment": 2455.61, "total_cost": 18299.14},
                {"year": 2024, "food": 5064.79, "housing": 7878.56, "energy": 1406.89, "transportation": 1969.64, "entertainment": 2527.28, "total_cost": 18843.16}
            ]
        },
        {
            "province_name": "Bangkok",
            "region": "กลาง",
            "image_file": read_image("static/images/Bangkok.png"),
            "cost_of_living": [
                {"year": 2020, "food": 6000, "housing": 9000, "energy": 2000, "transportation": 2500, "entertainment": 3000, "total_cost": 22500},
                {"year": 2021, "food": 6180, "housing": 9270, "energy": 2060, "transportation": 2575, "entertainment": 3090, "total_cost": 23175},
                {"year": 2022, "food": 6365.4, "housing": 9548.1, "energy": 2121.8, "transportation": 2652.25, "entertainment": 3182.7, "total_cost": 23870.25},
                {"year": 2023, "food": 6556.36, "housing": 9834.54, "energy": 2185.45, "transportation": 2731.82, "entertainment": 3278.18, "total_cost": 24586.36},
                {"year": 2024, "food": 6753.05, "housing": 10129.59, "energy": 2251.02, "transportation": 2813.77, "entertainment": 3376.52, "total_cost": 25324.95}
            ]
        }
    ]

    for province_data in data:
        new_province = Province(
            name=province_data["province_name"],
            region=province_data["region"],
            image_file=province_data["image_file"]
        )
        db.session.add(new_province)
        for cost_data in province_data["cost_of_living"]:
            new_cost = Cost_of_Living(
                province_name=province_data["province_name"],
                year=cost_data["year"],
                food=cost_data["food"],
                housing=cost_data["housing"],
                energy=cost_data["energy"],
                transportation=cost_data["transportation"],
                entertainment=cost_data["entertainment"],
                total_cost=cost_data["total_cost"]
            )
            db.session.add(new_cost)
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        add_data()