from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_, and_
import os
import uuid
from werkzeug.utils import secure_filename
from app import app, db
from app import oauth
from app.forms import LoginForm, RegistrationForm, ProductForm, EditProfileForm
from app.models import User, Product, CartItem, Message, ProductImage

@app.route("/")
@app.route("/index")
def index():
    products = Product.query.all()
    return render_template("index.html", title="Home", products=products)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        
        # NEW FIX: Check if the email is already in the database first!
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("That email is already registered. Please log in instead.", "danger")
            return redirect(url_for('register'))
            
        # If the email is unique, proceed with creating the account
        user = User(email=form.email.data, dota2_username=form.dota2_username.data, steam_id=form.steam_id.data if form.steam_id.data else None)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash("Account created! Welcome to BUYBACK.", "success")
        return redirect(url_for('login'))
        
    return render_template("register.html", title="Sign Up", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))
        login_user(user)
        flash(f"Welcome back, {user.dota2_username}.", "success")
        return redirect(url_for("index"))
    return render_template("login.html", title="Log In", form=form)

@app.route("/google/login")
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/google/auth")
def google_auth():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.userinfo()
    google_sub = user_info['sub']
    user_email = user_info['email']

    # Find user by Google ID
    user = User.query.filter_by(google_sub=google_sub).first()

    if not user:
        # If not found, find by email to link accounts
        user = User.query.filter_by(email=user_email).first()
        if user:
            # Link existing account
            user.google_sub = google_sub
            db.session.commit()
        else:
            # Create a new user
            new_username = user_info.get('name', user_email.split('@')[0])
            user = User(
                email=user_email,
                google_sub=google_sub,
                dota2_username=new_username
            )
            db.session.add(user)
            db.session.commit()
            flash("Your account has been created successfully. Please update your Steam ID in your profile settings.", "success")

    login_user(user)
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", title="Profile", user=current_user)

@app.route("/my_listings")
@login_required
def my_listings():
    my_listings = Product.query.filter_by(user_id=current_user.id).order_by(Product.id.desc()).all()
    return render_template("my_listings.html", title="My Listings", my_listings=my_listings)

@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data, price=form.price.data, rarity=form.rarity.data,
            status=form.status.data, quantity=form.quantity.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(new_product)

        # Handle file uploads
        uploaded_files = request.files.getlist('images') # Use 'images' as the field name
        for file in uploaded_files:
            if file and file.filename != '':
                # FIX: Generate a unique filename to prevent collisions
                _, ext = os.path.splitext(file.filename)
                filename = secure_filename(f"{uuid.uuid4()}{ext.lower()}") # Use uuid for unique filenames
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                new_image = ProductImage(image_filename=filename, product=new_product)
                db.session.add(new_image)

        db.session.commit()
        flash("Product listed successfully!", "success")
        return redirect(url_for("my_listings")) # Redirect to my_listings after adding
    return render_template("add_product.html", title="Sell Item", form=form)

@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.user_id != current_user.id: # Ensure current_user is the owner
        flash("You cannot delete someone else's product!", "danger")
        return redirect(url_for('my_listings'))
        
    db.session.delete(product)
    db.session.commit()
    flash(f"{product.name} has been removed from the marketplace.", "success")
    return redirect(url_for('my_listings'))

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", title=product.name, product=product)

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # Check if the new email is different and if it's already taken
        if form.email.data != current_user.email and User.query.filter_by(email=form.email.data).first(): # Check for duplicate email
            flash("This email address is already registered. Please use a different one or log in.", "danger")
            return render_template("edit_profile.html", title="Edit Profile", form=form)

        # NEW: Check current password for confirmation
        if not current_user.check_password(form.current_password.data):
            flash("Incorrect current password. Please verify your password and try again.", "danger")
            return render_template("edit_profile.html", title="Edit Profile", form=form)

        current_user.dota2_username = form.dota2_username.data
        current_user.steam_id = form.steam_id.data
        current_user.email = form.email.data

        db.session.commit()
        flash("Your profile changes have been saved successfully.", "success")
        return redirect(url_for("profile"))

    elif request.method == "GET":
        form.dota2_username.data = current_user.dota2_username
        form.steam_id.data = current_user.steam_id
        form.email.data = current_user.email
    return render_template("edit_profile.html", title="Edit Profile", form=form)

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Incorrect current password. Please verify your password and try again.", "danger")
            return render_template("change_password.html", title="Change Password", form=form)
        
        if form.new_password.data == form.current_password.data:
            flash("New password cannot be the same as the current password.", "warning")
            return render_template("change_password.html", title="Change Password", form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Your password has been updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html", title="Change Password", form=form)



@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.quantity <= 0:
        flash(f"Sorry, {product.name} is currently out of stock.", "danger")
        return redirect(url_for('index', _anchor='market-grid'))

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        if cart_item.quantity < product.quantity:
            cart_item.quantity += 1 # Increment quantity if item already in cart
            db.session.commit()
            flash(f"Another {product.name} added to your cart.", "success")
        else:
            flash(f"You cannot add more {product.name}. Max stock reached.", "warning")
    else:
        new_cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f"{product.name} added to your cart!", "success")
        
    return redirect(url_for('index', _anchor='market-grid'))

@app.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template("cart.html", title="Your Cart", cart_items=cart_items, total_price=total_price)

@app.route("/remove_from_cart/<int:cart_item_id>")
@login_required
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items: # Redirect if cart is empty
        flash("Your cart is empty!", "warning")
        return redirect(url_for('index'))
        
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        # Re-check stock before finalizing purchase to prevent overselling
        for item in cart_items:
            if item.product.quantity < item.quantity:
                flash(f"Sorry, the quantity for {item.product.name} has changed. There are only {item.product.quantity} left in stock.", "danger")
                return redirect(url_for('cart'))

        # If all items are in stock, proceed with the transaction
        for item in cart_items:
            product = Product.query.get(item.product_id)
            product.quantity -= item.quantity
            db.session.delete(item)
            
        db.session.commit()
        flash(f"Payment of ₱{total_price:,.2f} successful. Your order has been placed.", "success")
        return redirect(url_for('index'))
        
    return render_template("checkout.html", title="Checkout", total_price=total_price)

@app.route("/messages")
@login_required
def messages():
    active_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.deleted_by_sender == False),
            and_(Message.recipient_id == current_user.id, Message.deleted_by_recipient == False)
        )
    ).all()
    
    active_partner_ids = set()
    for msg in active_messages:
        if msg.sender_id != current_user.id:
            active_partner_ids.add(msg.sender_id)
        if msg.recipient_id != current_user.id:
            active_partner_ids.add(msg.recipient_id)
            
    other_users = User.query.filter(User.id.in_(active_partner_ids)).all()
    
    return render_template("messages.html", title="Inbox", other_users=other_users)

# ---> HERE IS THE MISSING ROUTE! <---
@app.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    """Renders the Vue.js chat room UI."""
    chat_partner = User.query.get_or_404(user_id)
    return render_template("chat.html", title=f"Chat with {chat_partner.dota2_username}", chat_partner=chat_partner)

@app.route("/api/chat/<int:user_id>")
@login_required
def api_get_chat(user_id):
    chat_history = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user_id, Message.deleted_by_sender == False),
            and_(Message.sender_id == user_id, Message.recipient_id == current_user.id, Message.deleted_by_recipient == False)
        )
    ).order_by(Message.timestamp.asc()).all()

    messages_data = []
    for msg in chat_history:
        messages_data.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "body": msg.body,
            "timestamp": msg.timestamp.isoformat() + "Z" # Send full UTC ISO string
        })
    return jsonify(messages_data)

@app.route("/api/products")
def api_products():
    products = Product.query.all()
    product_list = []
    for p in products:
        product_list.append({
            "id": p.id, "name": p.name, "price": p.price,
            "rarity": p.rarity, "status": p.status, 
            "quantity": p.quantity,
            "images": [url_for('static', filename=f'uploads/{img.image_filename}') for img in p.images]
        }) # Return all image URLs for the product
    return jsonify(product_list)

@app.route("/api/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def api_add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.quantity <= 0:
        return jsonify({"status": "error", "message": "Item is currently out of stock."})

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        if cart_item.quantity < product.quantity:
            cart_item.quantity += 1
            db.session.commit()
            return jsonify({"status": "success", "message": f"Another {product.name} added to cart!"})
        else:
            return jsonify({"status": "error", "message": "Maximum stock reached for this item."})
    else:
        new_cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(new_cart_item)
        db.session.commit()
        return jsonify({"status": "success", "message": f"{product.name} added to cart!"})
    
@app.route("/api/cart")
@login_required
def api_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    cart_list = []
    for item in cart_items:
        cart_list.append({
            "id": item.id,
            "quantity": item.quantity,
            "product": {
                "id": item.product.id,
                "name": item.product.name,
                "price": item.product.price,
                "rarity": item.product.rarity,
                # Use the first available image, or None if there are no images for display in cart
                "image_url": url_for('static', filename=f'uploads/{item.product.images[0].image_filename}') if item.product.images else None
            }
        })
    return jsonify(cart_list)

@app.route("/api/remove_from_cart/<int:cart_item_id>", methods=["POST"])
@login_required
def api_remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"status": "success", "message": "Item successfully removed from your cart."})
    return jsonify({"status": "error", "message": "Unauthorized access."}), 403

@app.route("/api/chat/<int:user_id>/send", methods=["POST"])
@login_required
def api_send_message(user_id):
    data = request.get_json()
    message_body = data.get("message")
    
    if message_body:
        msg = Message(sender_id=current_user.id, recipient_id=user_id, body=message_body)
        db.session.add(msg)
        db.session.commit()
        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Cannot send empty message"})

@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.user_id != current_user.id: # Ensure current_user is the owner
        flash("You cannot edit someone else's product!", "danger")
        return redirect(url_for('my_listings'))

    form = ProductForm()
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.rarity = form.rarity.data
        product.status = form.status.data
        product.quantity = form.quantity.data
        product.description = form.description.data
        
        # Handle new image uploads during edit
        uploaded_files = request.files.getlist(form.images.name)
        for file in uploaded_files:
            if file and file.filename != '': # Process new image uploads
                # FIX: Generate a unique filename to prevent collisions
                _, ext = os.path.splitext(file.filename)
                filename = secure_filename(f"{uuid.uuid4()}{ext.lower()}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_image = ProductImage(image_filename=filename, product=product)
                db.session.add(new_image)

        db.session.commit()
        flash(f"{product.name} has been updated successfully.", "success")
        return redirect(url_for('my_listings'))
        
    elif request.method == "GET":
        form.name.data = product.name
        form.price.data = product.price
        form.rarity.data = product.rarity
        form.status.data = product.status
        form.quantity.data = product.quantity
        form.description.data = product.description

    return render_template("edit_product.html", title="Edit Item", form=form, product=product)

@app.route("/delete_product_image/<int:image_id>", methods=["POST"])
@login_required
def delete_product_image(image_id):
    image_to_delete = ProductImage.query.get_or_404(image_id)
    
    # Ensure the current user owns the product associated with the image
    if image_to_delete.product.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized: You do not have permission to delete this image."}), 403

    # Construct the full path to the image file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete.image_filename)

    try:
        # Delete the file from the filesystem
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Delete the image record from the database
        db.session.delete(image_to_delete)
        db.session.commit()
        return jsonify({"status": "success", "message": "Image deleted successfully."}) # Return success message
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to delete image: {str(e)}"}), 500

@app.route("/api/chat/delete_conversation/<int:partner_id>", methods=["POST"])
@login_required
def api_delete_conversation(partner_id):
    chat_history = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == partner_id),
            and_(Message.sender_id == partner_id, Message.recipient_id == current_user.id)
        )
    ).all()
    
    for msg in chat_history:
        if msg.sender_id == current_user.id:
            msg.deleted_by_sender = True
        if msg.recipient_id == current_user.id:
            msg.deleted_by_recipient = True
            
        if msg.deleted_by_sender and msg.deleted_by_recipient:
            db.session.delete(msg)
            
    db.session.commit()
    return jsonify({"status": "success", "message": "Conversation history cleared successfully."})

@app.route("/api/update_cart/<int:cart_item_id>", methods=["POST"])
@login_required
def api_update_cart(cart_item_id):
    data = request.get_json()
    action = data.get("action")
    cart_item = CartItem.query.get_or_404(cart_item_id)

    if cart_item.user_id != current_user.id: # Ensure current_user owns the cart item
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    if action == "increase":
        if cart_item.quantity < cart_item.product.quantity:
            cart_item.quantity += 1
            db.session.commit()
            return jsonify({"status": "success", "new_quantity": cart_item.quantity})
        else: # Handle max stock reached
            return jsonify({"status": "error", "message": "Maximum stock reached for this item."})
            
    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
            return jsonify({"status": "success", "new_quantity": cart_item.quantity})
        else: # Handle min quantity
            return jsonify({"status": "error", "message": "Minimum quantity is 1. To remove the item, use the trash icon."})
            
    return jsonify({"status": "error", "message": "Invalid action for cart update."})