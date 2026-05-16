from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, Blueprint
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from sqlalchemy import or_, and_
import os
import uuid
import json
from werkzeug.utils import secure_filename
from app import db, oauth
from app.forms import LoginForm, RegistrationForm, ProductForm, EditProfileForm, ChangePasswordForm
from app.models import User, Product, CartItem, Message, ProductImage, PriceHistory, Order, Review

bp = Blueprint('main', __name__)

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        now = datetime.utcnow()
        if not current_user.last_seen or (now - current_user.last_seen).total_seconds() > 60:
            current_user.last_seen = now
            db.session.commit()

def _upload_image_to_storage(file_storage):
    """
    Uploads a file to the configured object storage (Supabase Storage) and returns the path.
    Returns None if the file is invalid or an error occurs.
    """
    if not file_storage or file_storage.filename == '':
        return None

    try:
        supabase_client = current_app.config['SUPABASE_CLIENT']
        bucket_name = current_app.config['SUPABASE_BUCKET']
        
        _, ext = os.path.splitext(file_storage.filename)
        # Use a unique filename without any folder prefix for a cleaner URL.
        file_path = f"{uuid.uuid4()}{ext.lower()}"
        
        file_bytes = file_storage.read()
        # Rewind the file pointer in case it needs to be read again
        file_storage.seek(0)
        supabase_client.storage.from_(bucket_name).upload(
            path=file_path, file=file_bytes, file_options={"content-type": file_storage.content_type}
        )
        return file_path
    except Exception as e:
        current_app.logger.error(f"Supabase upload failed: {e}")
        return None

@bp.route("/")
@bp.route("/index")
def index():
    products = Product.query.all()
    return render_template("index.html", title="Home", products=products)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, dota2_username=form.dota2_username.data, steam_id=form.steam_id.data if form.steam_id.data else None)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created successfully.", "success")
        return redirect(url_for('main.login'))
        
    return render_template("register.html", title="Sign Up", form=form)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password", "danger")
            return redirect(url_for('main.login'))
            
        # --- Auto-Promote Admin ---
        if user.email.strip().lower() == 'adsongalia@gbox.adnu.edu.ph' and not user.is_admin:
            user.is_admin = True
            db.session.commit()
        # --------------------------
            
        login_user(user) 
        flash("You have been logged in successfully.", "success")
        return redirect(url_for("main.index"))
    return render_template("login.html", title="Log In", form=form)

@bp.route("/google/login")
def google_login():
    redirect_uri = url_for('main.google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route("/google/auth")
def google_auth():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.userinfo()

    user, was_created = User.find_or_create_from_google(user_info)

    # --- Auto-Promote Admin ---
    if user.email.strip().lower() == 'adsongalia@gbox.adnu.edu.ph' and not user.is_admin:
        user.is_admin = True
    # --------------------------

    if was_created:
        db.session.add(user)
    
    db.session.commit()
    login_user(user)

    if was_created:
        flash("Welcome! Please complete your profile by setting your Dota 2 username and Steam ID.", "info")
        return redirect(url_for('main.edit_profile'))

    if not user.dota2_username or not user.steam_id:
        flash("Welcome back! We noticed your profile is incomplete. Please take a moment to update it.", "info")
        return redirect(url_for('main.edit_profile'))
        
    return redirect(url_for('main.index'))

@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("main.index"))

@bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", title="Profile", user=current_user)

@bp.route("/seller/<int:seller_id>")
def seller_profile(seller_id):
    seller = User.query.get_or_404(seller_id)
    # Fetch active listings for this seller
    products = Product.query.filter_by(user_id=seller.id).order_by(Product.id.desc()).all()
    
    has_bought = False
    if current_user.is_authenticated:
        has_bought = Order.query.filter_by(buyer_id=current_user.id, seller_id=seller_id).first() is not None

    return render_template("seller_profile.html", title=f"{seller.dota2_username}'s Profile", seller=seller, products=products, has_bought=has_bought)

@bp.route("/seller/<int:seller_id>/review", methods=["POST"])
@login_required
def add_review(seller_id):
    if current_user.id == seller_id:
        flash("You cannot review yourself.", "danger")
        return redirect(url_for('main.seller_profile', seller_id=seller_id))
    
    has_bought = Order.query.filter_by(buyer_id=current_user.id, seller_id=seller_id).first()
    if not has_bought:
        flash("You can only review sellers you have purchased from.", "danger")
        return redirect(url_for('main.seller_profile', seller_id=seller_id))

    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if not rating or rating < 1 or rating > 5:
        flash("Please provide a valid rating between 1 and 5.", "danger")
        return redirect(url_for('main.seller_profile', seller_id=seller_id))
        
    new_review = Review(seller_id=seller_id, buyer_id=current_user.id, rating=rating, comment=comment)
    db.session.add(new_review)
    flash("Your review has been submitted successfully.", "success")
        
    db.session.commit()
    return redirect(url_for('main.seller_profile', seller_id=seller_id))

@bp.route("/my_listings")
@login_required
def my_listings():
    my_listings = Product.query.filter_by(user_id=current_user.id).order_by(Product.id.desc()).all()
    return render_template("my_listings.html", title="My Listings", my_listings=my_listings)

@bp.route("/add_product", methods=["GET", "POST"])
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
        db.session.flush()  # Flush to assign an ID to new_product for the foreign key

        # BONUS 2: Add initial price to history
        initial_price = PriceHistory(product_id=new_product.id, price=new_product.price)
        db.session.add(initial_price)

        # Handle file uploads
        uploaded_files = request.files.getlist('images') # Use 'images' as the field name
        for file in uploaded_files:
            image_path = _upload_image_to_storage(file)
            if image_path:
                new_image = ProductImage(image_path=image_path, product=new_product)
                db.session.add(new_image)

        db.session.commit()
        flash("Your product has been listed successfully.", "success")
        return redirect(url_for("main.my_listings")) # Redirect to my_listings after adding
    return render_template("add_product.html", title="Sell Item", form=form)

@bp.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.user_id != current_user.id: # Ensure current_user is the owner
        flash("You cannot delete someone else's product!", "danger")
        return redirect(url_for('main.my_listings'))

    if Order.query.filter_by(product_id=product.id).first():
        flash("You cannot delete a product that has existing orders.", "danger")
        return redirect(url_for('main.my_listings'))

    # Delete associated cart items to prevent foreign key constraint failures
    CartItem.query.filter_by(product_id=product.id).delete()

    # Delete associated images from Supabase Storage
    try:
        supabase_client = current_app.config['SUPABASE_CLIENT']
        bucket_name = current_app.config['SUPABASE_BUCKET']
        paths_to_remove = [image.image_path for image in product.images]
        if paths_to_remove:
            supabase_client.storage.from_(bucket_name).remove(paths_to_remove)
    except Exception as e:
        current_app.logger.error(f"Could not delete product images from storage: {str(e)}")
        
    db.session.delete(product)
    db.session.commit()
    flash(f"'{product.name}' has been successfully deleted.", "success")
    return redirect(url_for('main.my_listings'))

@bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    # BONUS 3: Price comparison logic
    all_listings_same_name = Product.query.filter(Product.name == product.name).all()
    other_listings = sorted([p for p in all_listings_same_name if p.id != product.id], key=lambda x: x.price)

    is_cheapest = False
    if all_listings_same_name:
        min_price = min(p.price for p in all_listings_same_name)
        if product.price <= min_price:
            is_cheapest = True

    # Prepare price history data for the graph
    price_history_data = [
        {"timestamp": ph.timestamp.strftime('%b %d, %Y'), "price": ph.price}
        for ph in sorted(product.price_history, key=lambda x: x.timestamp)
    ]

    return render_template("product_detail.html", 
                           title=product.name, 
                           product=product,
                           other_listings=other_listings,
                           is_cheapest=is_cheapest,
                           price_history=price_history_data,
                           price_history_json=json.dumps(price_history_data)
                          )

@bp.route("/delete_profile_image", methods=["POST"])
@login_required
def delete_profile_image():
    if current_user.profile_image_path:
        try:
            supabase_client = current_app.config['SUPABASE_CLIENT']
            bucket_name = current_app.config['SUPABASE_BUCKET']
            supabase_client.storage.from_(bucket_name).remove([current_user.profile_image_path])
        except Exception as e:
            current_app.logger.error(f"Could not delete profile image: {e}")
        current_user.profile_image_path = None
        db.session.commit()
        flash("Your profile photo has been removed.", "success")
    return redirect(url_for("main.edit_profile"))

@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # If the user is changing their email, we MUST validate their password.
        if form.email.data != current_user.email:
            # Check if the new email is already taken
            if User.query.filter_by(email=form.email.data).first():
                flash("This email address is already registered. Please use a different one.", "danger")
                return render_template("edit_profile.html", title="Edit Profile", form=form)
            # Require current password to change email
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash("Incorrect password. You must provide your current password to change your email address.", "danger")
                return render_template("edit_profile.html", title="Edit Profile", form=form)

        current_user.dota2_username = form.dota2_username.data
        current_user.steam_id = form.steam_id.data
        current_user.email = form.email.data

        # Handle profile image upload
        profile_image_file = request.files.get('profile_image')
        if profile_image_file and profile_image_file.filename != '':
            image_path = _upload_image_to_storage(profile_image_file)
            if image_path:
                # Optionally delete old image from storage here to prevent clutter
                if current_user.profile_image_path:
                    try:
                        supabase_client = current_app.config['SUPABASE_CLIENT']
                        bucket_name = current_app.config['SUPABASE_BUCKET']
                        supabase_client.storage.from_(bucket_name).remove([current_user.profile_image_path])
                    except Exception as e:
                        current_app.logger.error(f"Could not delete old profile image: {e}")
                current_user.profile_image_path = image_path

        db.session.commit()
        flash("Your profile changes have been saved successfully.", "success")
        return redirect(url_for("main.profile"))

    elif request.method == "GET":
        form.dota2_username.data = current_user.dota2_username
        form.steam_id.data = current_user.steam_id
        form.email.data = current_user.email
    return render_template("edit_profile.html", title="Edit Profile", form=form)

@bp.route("/change_password", methods=["GET", "POST"])
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
        return redirect(url_for("main.profile"))

    return render_template("change_password.html", title="Change Password", form=form)



@bp.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template("cart.html", title="Your Cart", cart_items=cart_items, total_price=total_price)

@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    buy_now_product_id = request.args.get('buy_now_product_id', type=int)
    
    if buy_now_product_id:
        # --- Buy Now Logic ---
        product = Product.query.get_or_404(buy_now_product_id)
        
        if product.user_id == current_user.id:
            flash("You cannot buy your own items.", "danger")
            return redirect(url_for('main.product_detail', product_id=product.id))
            
        if product.quantity < 1:
            flash(f"Sorry, {product.name} is currently out of stock.", "danger")
            return redirect(url_for('main.product_detail', product_id=product.id))
            
        # Create a temporary CartItem object (not saved to DB) for consistent template logic
        buy_now_item = CartItem(product=product, quantity=1)
        cart_items = [buy_now_item]
        total_price = product.price
    else:
        # --- Standard Cart Checkout Logic ---
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash("Your cart is empty!", "warning")
            return redirect(url_for('main.index'))
        total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        if buy_now_product_id:
            # --- Finalize Buy Now ---
            try:
                # Lock the product row for update to prevent race conditions
                product_to_buy = Product.query.with_for_update().get_or_404(buy_now_product_id)
                if product_to_buy.quantity < 1:
                    flash(f"Sorry, {product_to_buy.name} is out of stock.", "danger")
                    return redirect(url_for('main.product_detail', product_id=product_to_buy.id))
                
                # Create an Order record
                new_order = Order(
                    buyer_id=current_user.id,
                    seller_id=product_to_buy.user_id,
                    product_id=product_to_buy.id,
                    quantity=1,
                    price_at_purchase=product_to_buy.price,
                    delivery_status='Pending'
                )
                db.session.add(new_order)
                product_to_buy.quantity -= 1
                db.session.commit()
                flash(f"Your order for ₱{product_to_buy.price:,.2f} has been placed successfully. The seller has been notified.", "success")
                return redirect(url_for('main.index'))
            except Exception as e:
                db.session.rollback()
                flash(str(e), "danger")
                return redirect(url_for('main.checkout', buy_now_product_id=buy_now_product_id))
        else:
            # --- Finalize Standard Cart ---
            try:
                # Re-query items within the transaction for safety, ordered by product_id to prevent deadlocks
                cart_items_from_db = CartItem.query.filter_by(user_id=current_user.id).order_by(CartItem.product_id).all()
                
                if not cart_items_from_db:
                    raise ValueError("Your cart is empty! Cannot proceed with checkout.")
                
                # Check stock for all items first
                out_of_stock_items = []
                for item in cart_items_from_db:
                    # Lock the product row for update to prevent race conditions
                    product = Product.query.with_for_update().get(item.product_id)
                    if product.quantity < item.quantity:
                        out_of_stock_items.append(product.name)
                
                if out_of_stock_items:
                    # This will trigger the rollback in the except block
                    raise ValueError(f"Sorry, the quantity for some items has changed: {', '.join(out_of_stock_items)}. Please review your cart.")

                # If all stock is good, proceed with creating orders and updating quantities
                for item in cart_items_from_db:
                    # Create an Order record for each item
                    new_order = Order(
                        buyer_id=current_user.id,
                        seller_id=item.product.user_id,
                        product_id=item.product.id,
                        quantity=item.quantity,
                        price_at_purchase=item.product.price,
                        delivery_status='Pending'
                    )
                    db.session.add(new_order)
                    item.product.quantity -= item.quantity
                    db.session.delete(item)
                
                db.session.commit()
                flash(f"Your order for ₱{total_price:,.2f} has been placed successfully. Sellers have been notified.", "success")
                return redirect(url_for('main.index'))
            except Exception as e:
                db.session.rollback()
                flash(str(e), "danger")
                return redirect(url_for('main.cart'))
        
    return render_template("checkout.html", title="Checkout", total_price=total_price, cart_items=cart_items)

@bp.route("/order_history")
@login_required
def order_history():
    orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template("order_history.html", title="Order History", orders=orders)

@bp.route("/messages")
@login_required
def messages():
    # Also fetch pending deliveries for the current user as a seller
    pending_deliveries_count = Order.query.filter_by(seller_id=current_user.id, delivery_status='Pending').count()

    # Find all unique users current_user has messaged or received messages from
    sent_to_ids = db.session.query(Message.recipient_id).filter(
        Message.sender_id == current_user.id, Message.deleted_by_sender == False
    ).distinct()
    received_from_ids = db.session.query(Message.sender_id).filter(
        Message.recipient_id == current_user.id, Message.deleted_by_recipient == False
    ).distinct()

    active_partner_ids = set([id for id, in sent_to_ids] + [id for id, in received_from_ids])
    
    conversations = []
    for partner_id in active_partner_ids:
        partner = User.query.get(partner_id)
        if not partner:
            continue

        latest_message = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == partner_id, Message.deleted_by_sender == False),
                and_(Message.sender_id == partner_id, Message.recipient_id == current_user.id, Message.deleted_by_recipient == False)
            )
        ).order_by(Message.timestamp.desc()).first()

        unread_count = Message.query.filter(
            Message.sender_id == partner_id,
            Message.recipient_id == current_user.id,
            Message.is_read == False,
            Message.deleted_by_recipient == False
        ).count()

        if latest_message:
            conversations.append({
                'partner': partner,
                'latest_message': latest_message,
                'unread_count': unread_count
            })
    
    conversations.sort(key=lambda c: c['latest_message'].timestamp, reverse=True)

    return render_template("messages.html", title="Inbox", conversations=conversations, pending_deliveries_count=pending_deliveries_count)

# ---> HERE IS THE MISSING ROUTE! <---
@bp.route("/chat/<int:user_id>")
@login_required
def chat(user_id):
    """Renders the Vue.js chat room UI."""
    chat_partner = User.query.get_or_404(user_id)
    return render_template("chat.html", title=f"Chat with {chat_partner.dota2_username}", chat_partner=chat_partner)

@bp.route("/seller_deliveries")
@login_required
def seller_deliveries():
    # Get all orders where the current user is the seller and delivery is pending
    pending_deliveries = Order.query.filter_by(seller_id=current_user.id, delivery_status='Pending').order_by(Order.order_date.asc()).all()
    return render_template("seller_deliveries.html", title="Pending Deliveries", deliveries=pending_deliveries)

@bp.route("/mark_delivered/<int:order_id>", methods=["POST"])
@login_required
def mark_delivered(order_id):
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash("You are not authorized to mark this order as delivered.", "danger")
        return redirect(url_for('main.seller_deliveries'))

    order.delivery_status = 'Delivered'
    
    # Automatically notify the buyer via chat
    auto_message = Message(
        sender_id=current_user.id,
        recipient_id=order.buyer_id,
        body=f"📦 Order Update: I have just delivered your order for '{order.product.name}'! Please verify and consider leaving a review on my profile. Thank you!",
        is_read=False
    )
    db.session.add(auto_message)
    
    db.session.commit()
    flash(f"Order {order.id} for {order.product.name} marked as delivered, and the buyer has been notified.", "success")
    return redirect(url_for('main.seller_deliveries'))

@bp.route("/api/chat/<int:user_id>")
@login_required
def api_get_chat(user_id):
    # Mark messages from this partner as read by the current user
    Message.query.filter(
        Message.sender_id == user_id,
        Message.recipient_id == current_user.id,
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()

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
        
    chat_partner = User.query.get(user_id)
    is_online = chat_partner.is_online() if chat_partner else False

    return jsonify({
        "messages": messages_data,
        "is_online": is_online
    })

@bp.route("/api/user_counts")
@login_required
def api_user_counts():
    return jsonify({
        "unread_count": current_user.unread_message_count(),
        "cart_count": current_user.cart_item_count()
    })

@bp.route("/api/products")
def api_products():
    products = Product.query.all()
    # Use a list comprehension and the new to_dict() method
    return jsonify([p.to_dict() for p in products])

@bp.route("/api/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def api_add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.user_id == current_user.id:
        return jsonify({"status": "error", "message": "You cannot add your own items to the cart."})

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
    
@bp.route("/api/cart")
@login_required
def api_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    return jsonify([item.to_dict() for item in cart_items])

@bp.route("/api/remove_from_cart/<int:cart_item_id>", methods=["POST"])
@login_required
def api_remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"status": "success", "message": "Item successfully removed from your cart."})
    return jsonify({"status": "error", "message": "Unauthorized access."}), 403

@bp.route("/api/chat/<int:user_id>/send", methods=["POST"])
@login_required
def api_send_message(user_id):
    data = request.get_json()
    message_body = data.get("message")
    
    if message_body:
        msg = Message(sender_id=current_user.id, recipient_id=user_id, body=message_body, is_read=False)
        db.session.add(msg)
        db.session.commit()
        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Cannot send empty message"})

@bp.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.user_id != current_user.id: # Ensure current_user is the owner
        flash("You cannot edit someone else's product!", "danger")
        return redirect(url_for('main.my_listings'))

    form = ProductForm()
    
    if form.validate_on_submit():
        # BONUS 2: Check if price changed to add to history
        if product.price != form.price.data:
            price_update = PriceHistory(product_id=product.id, price=form.price.data)
            db.session.add(price_update)

        product.name = form.name.data
        product.price = form.price.data
        product.rarity = form.rarity.data
        product.status = form.status.data
        product.quantity = form.quantity.data
        product.description = form.description.data
        
        # Handle new image uploads during edit
        uploaded_files = request.files.getlist(form.images.name)
        for file in uploaded_files:
            image_path = _upload_image_to_storage(file)
            if image_path:
                new_image = ProductImage(image_path=image_path, product=product)
                db.session.add(new_image)

        db.session.commit()
        flash(f"{product.name} has been updated successfully.", "success")
        return redirect(url_for('main.my_listings'))
        
    elif request.method == "GET":
        form.name.data = product.name
        form.price.data = product.price
        form.rarity.data = product.rarity
        form.status.data = product.status
        form.quantity.data = product.quantity
        form.description.data = product.description

    # Prepare images data for the template
    images_data = [
        {"id": img.id, "url": img.get_public_url()}
        for img in product.images
    ]

    return render_template("edit_product.html", title="Edit Item", form=form, product=product, images_data=images_data)

@bp.route("/delete_product_image/<int:image_id>", methods=["POST"])
@login_required
def delete_product_image(image_id):
    image_to_delete = ProductImage.query.get_or_404(image_id)
    
    # Ensure the current user owns the product associated with the image
    if image_to_delete.product.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized: You do not have permission to delete this image."}), 403

    try:
        # Delete the file from Supabase Storage
        supabase_client = current_app.config['SUPABASE_CLIENT']
        bucket_name = current_app.config['SUPABASE_BUCKET']
        # The image_path is stored in the database
        path_to_remove = image_to_delete.image_path
        supabase_client.storage.from_(bucket_name).remove([path_to_remove])

        # Delete the image record from the database
        db.session.delete(image_to_delete)
        db.session.commit()
        return jsonify({"status": "success", "message": "Image deleted successfully."}) # Return success message
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to delete image: {str(e)}"}), 500

@bp.route("/api/chat/delete_conversation/<int:partner_id>", methods=["POST"])
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

@bp.route("/api/update_cart/<int:cart_item_id>", methods=["POST"])
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

@bp.route("/admin/users")
@login_required
def admin_users():
    # Failsafe: Instant auto-promote if somehow missed during login
    if current_user.email.strip().lower() == 'adsongalia@gbox.adnu.edu.ph' and not current_user.is_admin:
        current_user.is_admin = True
        db.session.commit()

    # Secure the route - only admins can access
    if not current_user.is_admin:
        flash("You do not have permission to access the admin dashboard.", "danger")
        return redirect(url_for('main.index'))
        
    # Get the current page from the request args (default to 1), and paginate (10 users per page)
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.id.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template("admin_users.html", title="Admin - User Management", pagination=pagination)

@bp.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    # Secure the route
    if not current_user.is_admin:
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('main.index'))

    if user_id == current_user.id:
        flash("You cannot delete your own account from here.", "warning")
        return redirect(url_for('main.admin_users'))

    user_to_delete = User.query.get_or_404(user_id)

    try:
        # 1. Delete associated cart items and messages
        CartItem.query.filter_by(user_id=user_id).delete()
        Message.query.filter(or_(Message.sender_id == user_id, Message.recipient_id == user_id)).delete()
        # Delete associated reviews
        Review.query.filter(or_(Review.seller_id == user_id, Review.buyer_id == user_id)).delete()

        # 2. Delete associated orders (both as a buyer and seller)
        Order.query.filter(or_(Order.buyer_id == user_id, Order.seller_id == user_id)).delete()

        # 3. Delete associated products and their images
        products = Product.query.filter_by(user_id=user_id).all()
        supabase_client = current_app.config.get('SUPABASE_CLIENT')
        bucket_name = current_app.config.get('SUPABASE_BUCKET')

        for product in products:
            CartItem.query.filter_by(product_id=product.id).delete()
            Order.query.filter_by(product_id=product.id).delete()
            
            if supabase_client and bucket_name:
                paths_to_remove = [image.image_path for image in product.images]
                if paths_to_remove:
                    try:
                        supabase_client.storage.from_(bucket_name).remove(paths_to_remove)
                    except Exception as e:
                        current_app.logger.error(f"Could not delete product images from storage for product {product.id}: {str(e)}")
            db.session.delete(product)

        # 4. Finally, delete the user
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"User {user_to_delete.email} has been permanently deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the user: {str(e)}", "danger")

    return redirect(url_for('main.admin_users'))

@bp.route("/force_admin")
@login_required
def force_admin():
    # A direct backdoor route to forcefully grant admin rights to your email
    if current_user.email.strip().lower() == 'adsongalia@gbox.adnu.edu.ph':
        current_user.is_admin = True
        db.session.commit()
        flash("Admin access forcefully granted! Welcome to the dashboard.", "success")
        return redirect(url_for('main.admin_users'))
    flash("Unauthorized. This backdoor is restricted to the developer.", "danger")
    return redirect(url_for('main.index'))