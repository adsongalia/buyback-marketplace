import requests
import os
import uuid
from app import app, db
from app.models import Product, ProductImage

def seed_database():
    with app.app_context():
        # Clear existing data to prevent duplicates and orphaned images
        ProductImage.query.delete()
        Product.query.delete()
        
        dota_items = [
            {
                "name": "Manifold Paradox", "price": 1499.00, "rarity": "Arcana", "status": "Tradeable", "quantity": 5,
                "description": "With a raspy cackle, the elder smith Craler swung the sword that his family had spent eleven generations to fold and forge...",
                "image_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/arcana_phantom_assassin_manifold_paradox.png"
            },
            {
                "name": "Demon Eater", "price": 1267.00, "rarity": "Arcana", "status": "Tradeable", "quantity": 2,
                "description": "For long has Shadow Fiend gathered the souls of his enemies. Now, he has gathered the soul of a demon.",
                "image_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/arcana_shadow_fiend_demon_eater.png"
            },
            {
                "name": "Bladeform Legacy", "price": 3499.00, "rarity": "Arcana", "status": "Giftable", "quantity": 1,
                "description": "Yurnero’s mask has been cleaved in two, awakening the ancient souls that once lay dormant inside it.",
                "image_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/arcana_juggernaut_bladeform_legacy.png"
            },
            {
                "name": "Mace of Aeons", "price": 8500.00, "rarity": "Immortal", "status": "Tradeable", "quantity": 3,
                "description": "A weapon pulled from a fractured timeline where Faceless Void fell to a lesser champion.",
                "image_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/immortal_faceless_void_mace_of_aeons.png"
            },
            {
                "name": "Golden Silent Wake", "price": 450.00, "rarity": "Immortal", "status": "Tradeable", "quantity": 12,
                "description": "Drow Ranger's golden cape of pure silence.",
                "image_url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/immortal_drow_ranger_golden_silent_wake.png"
            }
        ]

        for item in dota_items:
            product = Product(
                name=item["name"],
                price=item["price"],
                rarity=item["rarity"],
                status=item["status"],
                quantity=item["quantity"],
                description=item["description"],
            )
            db.session.add(product)

            # Download and save the image
            if item.get("image_url"):
                try:
                    # Add a User-Agent header to mimic a browser request
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                    response = requests.get(item["image_url"], stream=True, headers=headers)
                    response.raise_for_status()

                    # Get extension from URL and create a unique filename
                    _, ext = os.path.splitext(item["image_url"])
                    filename = f"{uuid.uuid4()}{ext.lower()}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Create the ProductImage record
                    new_image = ProductImage(image_filename=filename, product=product)
                    db.session.add(new_image)

                except requests.exceptions.RequestException as e:
                    print(f"Warning: Could not download image for '{item['name']}'. Error: {e}")
            
        db.session.commit()
        print("Database seeded successfully with Dota 2 items.")

if __name__ == "__main__":
    seed_database()