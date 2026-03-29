from app import app, db
from app.models import Product

def seed_database():
    with app.app_context():
        # Clear existing products to prevent duplicates if you run this twice
        Product.query.delete()
        
        dota_items = [
            {
                "name": "Manifold Paradox", "price": 1499.00, "rarity": "Arcana", "status": "Tradeable", "quantity": 5,
                "description": "With a raspy cackle, the elder smith Craler swung the sword that his family had spent eleven generations to fold and forge...",
                "image_url": "https://community.cloudflare.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXQ9QVcJY8gulReQ0DFSua4xJ2DAhpsIQVGpu2vOQht3P3NIzRDvI2yxtnawKX1NriIlGgE6sYp0riSotWj3lCy-EttNTrwJIWWdgFoaVrXrFS-k7u8hJG-ucifmHJqpH_V/360fx360f"
            },
            {
                "name": "Demon Eater", "price": 1267.00, "rarity": "Arcana", "status": "Tradeable", "quantity": 2,
                "description": "For long has Shadow Fiend gathered the souls of his enemies. Now, he has gathered the soul of a demon.",
                "image_url": "https://community.cloudflare.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXQ9QVcJY8gulReQ0DFSua4xJ2DAhpsIAlGpuarIwhu2_b3YzxO4eO1kG-IlvHxI7rXqWdY781lxL-R9tT2jVK2qRY_ZGylctOVewY5YArR_Ve9wb-70MW47cyazSNhpH4i-z-DyGItHPEw/360fx360f"
            },
            {
                "name": "Bladeform Legacy", "price": 3499.00, "rarity": "Arcana", "status": "Giftable", "quantity": 1,
                "description": "Yurnero’s mask has been cleaved in two, awakening the ancient souls that once lay dormant inside it.",
                "image_url": "https://community.cloudflare.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXQ9QVcJY8gulReQ0DFSua4xJ2DAhpsIxlBpqe_Jg1p1_PNKzxA_sqwloqFlrj2MOqTkm5XvsZ0iL-QpdujjQGy8kNoZmryLNOSI1I8NFnf_AC9lri7hce66cvBwXpnuSRzsCncyyM2tcdP9g/360fx360f"
            },
            {
                "name": "Mace of Aeons", "price": 8500.00, "rarity": "Immortal", "status": "Tradeable", "quantity": 3,
                "description": "A weapon pulled from a fractured timeline where Faceless Void fell to a lesser champion.",
                "image_url": "https://community.cloudflare.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXQ9QVcJY8gulReQ0DFSua4xJ2DAhpsJAlOouewIQhp3vXNcz1D4sS7lYyPwa_1NeiFwDkH6ZNy0r2Wotij3gyxrUdkZmDwcNCdIVRqaFiH_1K_wu--gJG4upKbyCAwuCEnsHvemgv330__m0nF/360fx360f"
            },
            {
                "name": "Golden Silent Wake", "price": 450.00, "rarity": "Immortal", "status": "Tradeable", "quantity": 12,
                "description": "Drow Ranger's golden cape of pure silence.",
                "image_url": "https://community.cloudflare.steamstatic.com/economy/image/-9a81dlWLwJ2UUGcVs_nsVtzdOEdtWwKGZZLQHTxDZ7I56KU0Zwwo4NUX4oFJZEHLbXQ9QVcJY8gulReQ0DFSua4xJ2DAhpsIg5Cpb2oFA5t1vHNNjRD4s3HhoPTx7D1IuOEyz0GuZYgjriVrY_3jVWx-RJsN2-iIoSQd1A3NQmF-Fntle-8hMK1ucua1zI97Z1x5mGgnUMj/360fx360f"
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
                image_url=item["image_url"]
            )
            db.session.add(product)
            
        db.session.commit()
        print("Database seeded! Market is now full of Dota 2 items.")

if __name__ == "__main__":
    seed_database()