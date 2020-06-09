import base64
from io import BytesIO
import os
import uuid

from PIL import Image
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS

import cloudinary
import cloudinary.uploader
import cloudinary.api

from sqlalchemy import String, Integer, DateTime, Column, ForeignKey
from sqlalchemy.orm import relationship, backref

from marshmallow.fields import  Nested


from datetime import datetime

from config import Config

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
cors = CORS()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.Debug = True
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    @app.route("/api/meter")
    def get_meters():
        meter_data = MeterData.query.order_by(MeterData.created.desc()).all()

        return jsonify(
            status='success',
            message='Meter Data Found',
            data=MeterDataSchema(many=True).dump(meter_data)
        )

    @app.route("/api/meter", methods=["POST"])
    def add_meter_data():
        data = request.get_json()
        if not data:
            return jsonify(
                status='failed',
                message='No Data Was Sent'
            )

        if not data.get('name'):
            return jsonify(
                status='failed',
                message='Name is Required'
            )

        if not data.get('supervisor'):
            return jsonify(
                status='failed',
                message='Supervisor is Required'
            )

        if not data.get('meter_number'):
            return jsonify(
                status='failed',
                message='Meter Number is Required'
            )

        if not data.get('longitude'):
            return jsonify(
                status='failed',
                message='Longitude is Required'
            )

        if not data.get('latitude'):
            return jsonify(
                status='failed',
                message='Latitude is Required'
            )

        if not data.get('images'):
            return jsonify(
                status='failed',
                message='No Images Found'
            )

        meter_data = MeterData()
        meter_data.meter_number = data.get('meter_number')
        meter_data.name = data.get('name')
        meter_data.supervisor = data.get('supervisor')
        meter_data.latitude = data.get('latitude')
        meter_data.longitude = data.get('longitude')

        db.session.add(meter_data)
        for image in data.get('image'):
            unique_filename = str(uuid.uuid4()) + '.' + data['type'].lower()

            save_image(
                unique_filename,
                image['img'],
                Config.IMAGE_UPLOAD_FOLDER,
                Config.IMAGE_SIZE
            )
            img = MeterImage()
            img.image = unique_filename
            image.meter_data = meter_data
            db.session.add(img)

        db.session.commit()

    return app


class MeterData(db.Model):
    id = Column(Integer, primary_key=True)
    meter_number = Column(String(100), nullable=False, unique=True)
    name = Column(String(300), nullable=False)
    longitude = Column(String(200))
    latitude = Column(String(200))
    supervisor = Column(String(300), nullable=False)
    created = Column(DateTime, default=datetime.utcnow())

    meter_images = relationship('MeterImage', backref=backref("meter_data", lazy=True))


class MeterImage(db.Model):
    id = Column(Integer, primary_key=True)
    meter_data_id = Column(Integer, ForeignKey("meter_data.id", ondelete='CASCADE'))
    image = Column(String(200), nullable=False)
    created = Column(DateTime, default=datetime.utcnow())


class MeterDataSchema(ma.SQLAlchemySchema):
    class Meta:
        table = MeterData.__table__

    meter_images = Nested("MeterImageSchema", many=True, only=["id", "first_name", "last_name", "email", "phone", "image_url"])


class MeterImageSchema(ma.SQLAlchemySchema):
    class Meta:
        table = MeterImage.__table__


def resize_image(img, path, size, crop, thumb, filename):
    new_height, new_width = size
    width, height = img.size

    height_ratio = height / new_height
    width_ratio = width / new_width

    optimal_ratio = width_ratio
    if height_ratio < width_ratio:
        optimal_ratio = height_ratio

    optimal_size = (int(width / optimal_ratio), int(height / optimal_ratio))
    img = img.resize(optimal_size)

    if crop:
        width, height = img.size

        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2

        img = img.crop((left, top, right, bottom))

    img.save(path)


def save_image(filename, image64, upload_folder, upload_size, crop=False, thumb=False):
    path = os.path.join(upload_folder, filename)
    img = Image.open(BytesIO(base64.b64decode(image64)))

    resize_image(img, path, upload_size, crop, thumb, filename)
    cloudinary.uploader.upload(path)
