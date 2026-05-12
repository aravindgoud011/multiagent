from app.backend.extensions import get_db_connection
import datetime

class SupportAgent:
    """
    Support Agent: Handles customer queries about shop status, product availability,
    and purchase intent.
    """

    def get_shop_status(self):
        """Returns whether the shop is open or closed."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT [value] FROM settings WHERE [key] = 'shop_status'")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "open"

    def check_product_availability(self, product_name):
        """Checks if a product is in stock and notifies admin if not."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use LIKE for flexible matching
        cursor.execute("SELECT name, stock, unit FROM product WHERE name LIKE ?", f"%{product_name}%")
        product = cursor.fetchone()
        
        if product:
            if product.stock > 0:
                conn.close()
                return f"Yes, {product.name} is available! We have {product.stock} {product.unit} in stock."
            else:
                self._notify_admin_of_interest(product_name, "out_of_stock")
                conn.close()
                return f"I'm sorry, {product.name} is currently out of stock. I've notified the shopkeeper that you're looking for it!"
        else:
            self._notify_admin_of_interest(product_name, "not_found")
            conn.close()
            return f"I couldn't find '{product_name}' in our inventory. I've sent a request to the shopkeeper to check if they can get it for you!"

    def handle_purchase_intent(self, customer_name, full_query):
        """Checks availability for multiple products and notifies admin."""
        import re
        
        # 1. Extract potential product names more safely
        # Only replace WHOLE words to avoid mangling (e.g. 'a' in 'rice')
        clean = full_query.lower()
        filler_words = ["i", "want", "to", "buy", "coming", "shop", "am", "a", "for", "please", "some"]
        for word in filler_words:
            clean = re.sub(r'\b' + word + r'\b', '', clean)
        
        # Replace 'and' with comma for splitting
        clean = re.sub(r'\band\b', ',', clean)
        
        # Split by comma and clean up
        raw_items = [i.strip() for i in clean.split(",") if i.strip()]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        available = []
        unavailable = []
        
        for raw_item in raw_items:
            # 1. Try EXACT match first (e.g. "oil 5kg")
            cursor.execute("SELECT name, stock FROM product WHERE name LIKE ?", f"%{raw_item}%")
            row = cursor.fetchone()
            
            if row and row.stock > 0:
                # Found exact or very close match
                available.append(row.name)
            else:
                # 2. Try partial match (flexible spacing)
                import re
                search_term = re.sub(r'[\d\-\.\s]+(kg|litre|l|ml|g|pcs|packet|pk|units)?$', '', raw_item).strip()
                if not search_term: search_term = raw_item
                
                # Make search flexible (chilli powder vs chillipowder)
                # Try with wildcards between characters if it's a single word
                flexible_term = f"%{search_term}%"
                if " " not in search_term:
                    # If it's like "chillipowder", try matching "chilli%powder"
                    # Simple heuristic: if it contains "powder", "oil", "milk" etc.
                    for keyword in ["powder", "oil", "milk", "tea", "soap", "chilli"]:
                        if keyword in search_term and search_term != keyword:
                            flexible_term = f"%{search_term.replace(keyword, '%' + keyword)}%"
                            break

                cursor.execute("SELECT name, stock FROM product WHERE name LIKE ?", flexible_term)
                partial_row = cursor.fetchone()
                
                if partial_row and partial_row.stock > 0:
                    # Final Relevance Check: make sure the found name actually relates to the search term
                    # This prevents random matches like 'GaramMasala' if it didn't actually contain the search word
                    found_name = partial_row.name.lower()
                    if any(word in found_name for word in search_term.split()):
                        available.append(f"{partial_row.name} (Note: you asked for '{raw_item}')")
                    else:
                        unavailable.append(raw_item)
                else:
                    unavailable.append(raw_item)
        
        conn.close()
        
        response_msg = ""
        if available:
            response_msg += f"✅ **Available:** {', '.join(available)}. I've told the shopkeeper to keep these ready for you! "
        if unavailable:
            response_msg += f"\n❌ **Out of Stock/Not Found:** {', '.join(unavailable)}. I've notified the shopkeeper that you're looking for these."
            
        summary = f"Customer '{customer_name}' is coming. \nAvailable: {', '.join(available) if available else 'None'}\nMissing: {', '.join(unavailable) if unavailable else 'None'}"
        self._send_notification("Incoming Customer", summary)
        
        return response_msg if response_msg else "I've noted your request and shared it with the shopkeeper!"

    def _notify_admin_of_interest(self, product_name, reason):
        """Internal helper to notify admin when a customer asks for a missing product."""
        title = "Product Interest"
        if reason == "out_of_stock":
            msg = f"A customer just asked for '{product_name}', but it is currently out of stock."
        else:
            msg = f"A customer just asked for '{product_name}', which is not in our inventory."
        self._send_notification(title, msg)

    def _send_notification(self, title, message):
        """Sends a notification to the admin users."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find admin IDs
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = [row[0] for row in cursor.fetchall()]
        
        for admin_id in admins:
            cursor.execute(
                "INSERT INTO notification (title, message, user_id, is_read, created_at) VALUES (?, ?, ?, 0, ?)",
                title, message, admin_id, datetime.datetime.utcnow()
            )
        
        conn.commit()
        conn.close()

    def process_query(self, user_query, customer_name="Customer"):
        """Main entry point for processing customer chat queries."""
        query = user_query.lower().strip()
        
        # 0. Greetings
        if query in ["hi", "hello", "hey", "hola", "greetings"]:
            return f"Hello {customer_name}! How can I help you today?"

        # 1. Shop Status Queries
        if any(k in query for k in ["shop open", "is it open", "shop status"]):
            status = self.get_shop_status()
            return f"The shop is currently **{status.upper()}**."
            
        # 2. Purchase Intent
        if any(k in query for k in ["buy", "coming", "want", "need", "get", "order", "give"]):
            return self.handle_purchase_intent(customer_name, user_query)

        # 3. Product Availability (Better extraction)
        availability_keywords = ["available", "have", "stock", "is there", "get", "has"]
        is_asking_availability = any(k in query for k in availability_keywords)
        
        if is_asking_availability or (len(query.split()) <= 3 and len(query) > 2):
            # Try to extract product name
            clean_query = query
            for k in availability_keywords + ["is", "the", "a", "any", "do", "you", "of"]:
                clean_query = clean_query.replace(f" {k} ", " ").replace(f"{k} ", "").replace(f" {k}", "")
            
            product_target = clean_query.replace("?", "").replace(".", "").strip()
            
            # Extra safety: don't match if target is too short or just a filler
            if product_target and len(product_target) > 2:
                return self.check_product_availability(product_target)
            
        # 4. Randomized Fallback
        import random
        fallbacks = [
            "I'm sorry, I didn't quite catch that. Could you try rephrasing?",
            "I'm not sure I follow. Could you say that a different way?",
            "Apologies, I didn't quite get that.",
            "I'm still learning! Could you try asking that differently?",
            f"Sorry {customer_name}, I didn't understand that query."
        ]
        return random.choice(fallbacks)

support_agent = SupportAgent()
