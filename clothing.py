import sys
import os
import re
import pyodbc
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QListWidget, QListWidgetItem, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from PyQt6 import uic

# Database Connection Class
class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            # Use Windows Authentication (no username and password needed)
            connection_string = (
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=DESKTOP-CD2HEHV\SPARTA;'    
                'DATABASE=Clothing;'
                'Trusted_Connection=yes;'
            )
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            print("Connected to the database successfully.")
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")
            return None
        return self.cursor

    def close(self):
        if self.connection:
            self.connection.close()

# Signup Window Class
class SignupWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('signup.ui', self)  # Load the signup.ui file dynamically
        self.db = DatabaseConnection()
        self.Signup_button.clicked.connect(self.signup)

    def signup(self):
        # Get user input from UI
        first_name = self.first_name.text()
        last_name = self.last_name.text()
        email = self.email.text()
        password = self.password.text()

        # Check if inputs are valid
        if not first_name or not last_name or not email or not password:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields")
            return

        cursor = self.db.connect()
        if cursor:
            try:
                cursor.execute("""
                    INSERT INTO Customer (first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?)
                """, (first_name, last_name, email, password))
                self.db.connection.commit()
                QMessageBox.information(self, "Success", "Account created successfully")
                
                # Close signup window and show login window
                self.close()

                # Open the Login Window after successful sign up
                self.login_window = LoginWindow()
                self.login_window.show()
                
            except pyodbc.Error as e:
                QMessageBox.warning(self, "Database Error", f"Error: {e}")
            finally:
                self.db.close()

# Login Window Class
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)  # Load the login.ui file dynamically
        self.db = DatabaseConnection()
        self.Login_button.clicked.connect(self.login)

        self.Signup_button.clicked.connect(self.openSignup)

    def openSignup(self):
        self.close()
        self.sign = SignupWindow()
        self.sign.show()

    def login(self):
        # Get user input from UI
        email = self.email.text()  # Ensure matching field names
        password = self.password.text()  # Ensure matching field names

        # Check if inputs are valid
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter valid information")
            return

        cursor = self.db.connect()
        if cursor:
            try:
                cursor.execute("""
                    SELECT * FROM Customer WHERE email = ? AND password = ?
                """, (email, password))
                result = cursor.fetchone()
                if result:
                    # Retrieve customer_id and customer_name from the result
                    customer_id = result[0]  # Assuming customer_id is the first column
                    customer_name = result[1]  # Assuming customer_name is the second column
                    
                    QMessageBox.information(self, "Login Success", "Login successful")
                    self.close()  # Close login window
                    
                    # Pass customer_id and customer_name to BrowseWindow
                    self.browse_window = BrowseWindow(customer_id, customer_name)  # Create an instance of the Browse window
                    self.browse_window.show()  # Show the Browse window

                else:
                    QMessageBox.warning(self, "Login Error", "Invalid email or password")
            except pyodbc.Error as e:
                QMessageBox.warning(self, "Database Error", f"Error: {e}")
            finally:
                self.db.close()

# Browse Window Class (browse.ui)
class BrowseWindow(QMainWindow):
    def __init__(self, customer_id, customer_name):
        super().__init__()
        uic.loadUi('browse.ui', self)  # Load the browse.ui file dynamically
        self.customer_id = customer_id
        self.customer_name = customer_name

        # Connect the QPushButtons to open_product_window
        self.Mens_Wear.clicked.connect(lambda: self.open_product_window("Mens_Wear"))
        self.womens.clicked.connect(lambda: self.open_product_window("Womens"))

    def open_product_window(self, category_name):
        category_id = self.get_category_id(category_name)
        if category_id is not None:
            self.close()
            self.product_window = ProductWindow(category_id, self.customer_id, self.customer_name)
            self.product_window.show()

    def get_category_id(self, category_name):
        cursor = DatabaseConnection().connect()
        if cursor:
            try:
                cursor.execute("""
                    SELECT category_id FROM Category WHERE category_name = ?
                """, (category_name,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    QMessageBox.warning(self, "Category Not Found", "Category not found in the database.")
            except pyodbc.Error as e:
                QMessageBox.warning(self, "Database Error", f"Error: {e}")
            finally:
                DatabaseConnection().close()
        return None


class ProductWindow(QMainWindow):
    def __init__(self, category_id, customer_id, customer_name):
        super().__init__()
        uic.loadUi('product.ui', self)  
        self.category_id = category_id  
        self.customer_id = customer_id  # Store customer_id
        self.customer_name = customer_name  # Store customer_name
        self.display_products()

    def display_products(self):
        cursor = DatabaseConnection().connect()
        if cursor:
            try:
                cursor.execute("""
                    SELECT product_id, product_name, price, color, size, description
                    FROM Product WHERE category_id = ?
                """, (self.category_id,))
                products = cursor.fetchall()

                self.product_list.clear()

                # Loop through products and display in QListWidget
                for product in products:
                    product_id = product[0]  # Capture product_id
                    product_name = product[1]
                    price = product[2]
                    color = product[3]
                    size = product[4]
                    des = product[5]

                    # Create QListWidgetItem for each product
                    item_widget = QWidget() 
                    layout = QVBoxLayout(item_widget)

                    # Display product image
                    image_path = self.get_image_path(product_name)
                    product_image_label = QLabel()
                    if image_path:
                        pixmap = QPixmap(image_path)
                        product_image_label.setPixmap(pixmap)
                        product_image_label.setScaledContents(True)

                    # Display product name and price
                    product_info_label = QLabel(f"{product_name} - ${price}")

                    # Add image and text to layout
                    layout.addWidget(product_image_label)
                    layout.addWidget(product_info_label)

                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())  
                    self.product_list.addItem(item) 
                    self.product_list.setItemWidget(item, item_widget) 

                    # Corresponding image file for each product
                    image_path = self.get_image_path(product_name)

                    # Connect item click to open product details window
                    item_widget.mousePressEvent = lambda event, product_id=product_id, product_name=product_name, price=price, color=color, size=size, des=des, image_path=image_path: self.open_product_details(event, product_id, product_name, price, color, size, des, image_path)

                    if image_path:
                        # Set product image
                        product_image = QLabel()
                        pixmap = QPixmap(image_path)
                        scaled_pixmap = pixmap.scaled(300, 300, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)  # Scale to 100x100
                        product_image.setPixmap(scaled_pixmap)
                        product_image.setScaledContents(True)

                        # Add the product to the list
                        self.product_list.addItem(item)
                        item.setSizeHint(product_image.sizeHint())
                    else:
                        print(f"No image found for {product_name}")

            except pyodbc.Error as e:
                QMessageBox.warning(self, "Database Error", f"Error: {e}")
            finally:
                DatabaseConnection().close()

    def open_product_details(self, event, product_id, product_name, price, color, size, des, image_path):
        # Open the product details window when a product item is clicked, passing the product_id as well
        self.product_details_window = ProductDetailsWindow(product_id, product_name, price, color, size, des, image_path, self.customer_name, self.customer_id)
        self.product_details_window.show()

    def get_image_path(self, product_name):
        """Generate the image file path based on product name."""
        image_folder = r'C:\Users\ibrahim\Desktop\Clothing\images' 
        sanitized_product_name = re.sub(r'\s+', '_', product_name)  
        sanitized_product_name = re.sub(r'[^\w_]', '', sanitized_product_name)
        image_filename = f"{sanitized_product_name}.jpg"  
        image_path = os.path.join(image_folder, image_filename)
        
        if os.path.exists(image_path):
            return image_path
        else:
            print(f"No image found for {product_name}, trying lowercase...")
            sanitized_product_name = sanitized_product_name.lower()  
            image_filename = f"{sanitized_product_name}.jpg"
            image_path = os.path.join(image_folder, image_filename)

            if os.path.exists(image_path):
                return image_path
            return None

class ProductDetailsWindow(QMainWindow):
    cart = []  # List to store cart items
    total_price = 0.0  # Variable to store total price
    
    def __init__(self, product_id, product_name, price, color, size, des, image_path, customer_name, customer_id):
        super().__init__()
        uic.loadUi('product_details.ui', self)  # Load the product details UI file dynamically
        
        self.product_id = product_id  # Store product_id
        self.customer_name = customer_name  # Store customer_name
        self.customer_id = customer_id  # Store customer_id

        self.product_name_label.setText(product_name)
        self.price_label.setText(f"${price}")
        self.color_label.setText(f"Color: {color}") 
        self.size_label.setText(f"Size: {size}") 
        self.des_label.setText(f"{des}")

        if image_path:
            pixmap = QPixmap(image_path)
            self.product_image_label.setPixmap(pixmap)
            self.product_image_label.setScaledContents(True)
        else:
            self.product_image_label.setText("No image available")

        self.add.clicked.connect(self.add_to_cart)  # Add item to cart
        self.check.clicked.connect(self.checkout)  # Proceed to checkout

        self.product_details = {
            'product_id': product_id,  # Store product_id
            'product_name': product_name,
            'price': price,
            'image_path': image_path
        }

    def add_to_cart(self):
        price = float(self.product_details['price'])

        # Add the current product to the cart
        self.cart.append(self.product_details)
        ProductDetailsWindow.total_price += price
        
        # Optionally show a message confirming the item was added
        QMessageBox.information(self, "Added to Cart", f"{self.product_details['product_name']} has been added to your cart.")
        
    def checkout(self):
        self.close()  # Close the current window
        
        # Create and show the Checkout window, passing the cart and total price
        self.checkout_window = CheckoutWindow(self.cart, self.total_price, self.customer_name, self.customer_id)
        self.checkout_window.show()

class CheckoutWindow(QMainWindow):
    def __init__(self, cart, total_price, customer_name, customer_id):
        super().__init__()
        uic.loadUi('checkout.ui', self)  # Load the checkout UI file dynamically
        self.cart = cart
        self.total_price = total_price
        self.customer_name = customer_name
        self.customer_id = customer_id
        self.update_cart_display()
        self.place.clicked.connect(self.place_order)  # Connect Place Order button to the method

    def update_cart_display(self):
        self.cart_list.clear()  # Clear any previous items
        
        for item in self.cart:
            product_name = item['product_name']
            price = item['price']
            item_text = f"{product_name} - ${price}"

            # Create QListWidgetItem for each cart item
            item_widget = QListWidgetItem(item_text)
            self.cart_list.addItem(item_widget)

        # Update the total price label
        self.total.setText(f"Total: ${self.total_price}")

    def place_order(self):
        cursor = DatabaseConnection().connect()
        if cursor:
            try:
                # Insert the order details into the Order table
                cursor.execute("""
                    INSERT INTO Orders (customer_name, total_price)
                    VALUES (?, ?)
                    """, (self.customer_name, self.total_price))

                # Get the last inserted order_id using SCOPE_IDENTITY()
                cursor.execute("SELECT SCOPE_IDENTITY()")
                order_id = cursor.fetchone()[0]

                for item in self.cart:
                # Insert product_id into OrderDetails table
                    cursor.execute("""
                        INSERT INTO OrderDetails (order_id, product_id, product_name, price)
                        VALUES (?, ?, ?, ?)
                        """, (order_id, item['product_id'], item['product_name'], item['price']))
            
            # Commit the transaction only if the connection is valid
                if cursor.connection:
                    cursor.connection.commit()
                    QMessageBox.information(self, "Order Placed", "Your order has been placed successfully!")
                else:
                    QMessageBox.warning(self, "Database Error", "Failed transaction.")
                self.close()

            except pyodbc.Error as e:
                QMessageBox.warning(self, "Database Error", f"Error: {e}")
            finally:
                DatabaseConnection().close()
        else:
            QMessageBox.warning(self, "Database Error", "Database connection failed.")



if __name__ == "__main__":
    app = QApplication([]) 
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
