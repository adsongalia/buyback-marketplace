from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required # NEW
from app import app, db
from app.forms import LoginForm, RegistrationForm, ProductForm, EditProfileForm
from app.models import User, Product, CartItem

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
        user = User(email=form.email.data, dota2_username=form.dota2_username.data, steam_id=form.steam_id.data)
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
        login_user(user) # THIS officially logs them in
        flash(f"Welcome back, {user.dota2_username}!", "success")
        return redirect(url_for("index"))
    return render_template("login.html", title="Log In", form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    # This grabs the products listed by the logged-in user
    my_listings = Product.query.filter_by(user_id=current_user.id).all()
    return render_template("profile.html", title="Profile", user=current_user, my_listings=my_listings)

# UPDATE THIS ROUTE: Tag the seller when adding a product
@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data, price=form.price.data, rarity=form.rarity.data,
            status=form.status.data, quantity=form.quantity.data,
            description=form.description.data, image_url=form.image_url.data,
            user_id=current_user.id # NEW: Tags the product to the logged-in user
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product listed successfully!", "success")
        return redirect(url_for("index"))
    return render_template("add_product.html", title="Sell Item", form=form)


# NEW ROUTE: The Midterm CRUD "Delete" Operation
@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Security check: Only the owner can delete it
    if product.user_id != current_user.id:
        flash("You cannot delete someone else's product!", "danger")
        return redirect(url_for('profile'))
        
    db.session.delete(product)
    db.session.commit()
    flash(f"{product.name} has been removed from the marketplace.", "success")
    return redirect(url_for('profile'))

# NEW ROUTE: Detailed Product View
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", title=product.name, product=product)

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.dota2_username = form.dota2_username.data
        current_user.steam_id = form.steam_id.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your changes have been saved.", "success")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        # Pre-fill the form with the user's current data
        form.dota2_username.data = current_user.dota2_username
        form.steam_id.data = current_user.steam_id
        form.email.data = current_user.email
    return render_template("edit_profile.html", title="Edit Profile", form=form)

@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.quantity <= 0:
        flash(f"Sorry, {product.name} is out of stock!", "danger")
        return redirect(url_for('index', _anchor='market-grid')) # ADDED _anchor

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        if cart_item.quantity < product.quantity:
            cart_item.quantity += 1
            db.session.commit()
            flash(f"Added another {product.name} to your cart.", "success")
        else:
            flash(f"You cannot add more {product.name}. Max stock reached.", "warning")
    else:
        new_cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f"{product.name} added to your cart!", "success")
        
    return redirect(url_for('index', _anchor='market-grid')) # ADDED _anchor

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
    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('index'))
        
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        # Simulate payment processing & inventory deduction
        for item in cart_items:
            product = Product.query.get(item.product_id)
            product.quantity -= item.quantity # Deduct from stock
            db.session.delete(item) # Remove from cart
            
        db.session.commit()
        flash(f"Payment of ₱{total_price:,.2f} successful! Aegis secured.", "success")
        return redirect(url_for('index'))
        
    return render_template("checkout.html", title="Checkout", total_price=total_price)

@app.route("/messages")
@login_required
def messages():
    # Grab all users EXCEPT the current user to display as "Available Chats"
    # (In a massive app, you'd only query recent chats, but this is perfect for your prototype!)
    other_users = User.query.filter(User.id != current_user.id).all()
    return render_template("messages.html", title="Inbox", other_users=other_users)

@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):
    chat_partner = User.query.get_or_404(user_id)
    
    # If the user typed a message and hit send
    if request.method == "POST":
        message_body = request.form.get("message")
        if message_body:
            msg = Message(sender_id=current_user.id, recipient_id=chat_partner.id, body=message_body)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('chat', user_id=chat_partner.id))

    # Fetch the back-and-forth history between these two specific users
    from sqlalchemy import or_, and_
    chat_history = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == chat_partner.id),
            and_(Message.sender_id == chat_partner.id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    return render_template("chat.html", title=f"Chat with {chat_partner.dota2_username}", chat_partner=chat_partner, chat_history=chat_history)