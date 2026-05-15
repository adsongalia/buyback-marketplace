from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    dota2_username = db.Column(db.String(80))
    steam_id = db.Column(db.String(80))
    google_sub = db.Column(db.String(255), unique=True, nullable=True)
    purchases = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy='dynamic')
    sales = db.relationship('Order', foreign_keys='Order.seller_id', backref='seller', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def find_or_create_from_google(cls, user_info):
        """Finds an existing user or creates a new one from Google OAuth info."""
        google_sub = user_info['sub']
        user_email = user_info['email']

        # Find user by Google ID first
        user = cls.query.filter_by(google_sub=google_sub).first()
        if user:
            return user, False  # Return user and "was not created" flag

        # If not found, find by email to link accounts
        user = cls.query.filter_by(email=user_email).first()
        if user:
            user.google_sub = google_sub
            return user, False # Return user and "was not created" flag

        # If no user found, create a new one
        new_username = user_info.get('name', user_email.split('@')[0])
        user = cls(email=user_email, google_sub=google_sub, dota2_username=new_username)
        return user, True # Return user and "was created" flag


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rarity = db.Column(db.String(50))
    status = db.Column(db.String(50)) 
    quantity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    
    # NEW: Link product to the seller
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    seller = db.relationship('User', backref=db.backref('my_products', lazy=True))

    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade="all, delete-orphan")
    price_history = db.relationship('PriceHistory', backref='product', lazy=True, cascade="all, delete-orphan")

    def get_first_image_url(self):
        if not self.images:
            return None
        from flask import current_app
        try:
            image_path = self.images[0].image_path
            supabase_client = current_app.config['SUPABASE_CLIENT']
            bucket_name = current_app.config['SUPABASE_BUCKET']
            return supabase_client.storage.from_(bucket_name).get_public_url(image_path)
        except Exception as e:
            current_app.logger.error(f"Error generating public URL: {e}")
            return None

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price,
                "rarity": self.rarity, "status": self.status, "quantity": self.quantity,
                "image_url": self.get_first_image_url()}

    def __repr__(self):
        return f"<Product {self.name}>"

class ProductImage(db.Model):
    __tablename__ = "product_images"
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

class PriceHistory(db.Model):
    __tablename__ = "price_history"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product')

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            "product": self.product.to_dict()
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # NEW: Soft-Delete Flags
    deleted_by_sender = db.Column(db.Boolean, default=False)
    deleted_by_recipient = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delivery_status = db.Column(db.String(50), default='Pending', nullable=False)

    product = db.relationship('Product', backref='orders')

    def __repr__(self):
        return f"<Order {self.id} - Product: {self.product.name} - Buyer: {self.buyer.email}>"