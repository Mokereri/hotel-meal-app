# mpesa_callback_handler.py
from flask import Flask, request, jsonify
from decouple import config
import mysql.connector
from datetime import datetime
import json
import logging

app = Flask(__name__)

# Configure logging for the Flask app. This helps in debugging by printing messages
# to the terminal where the Flask app is running.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==== Database Functions for Callback Handler ====
# These functions interact with the MySQL database, using credentials from .env.
# This is a shared resource between your Flask app and Streamlit app, which is intended.
def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=config("DB_HOST"),        # Reads DB_HOST from .env
            user=config("DB_USER"),        # Reads DB_USER from .env
            password=config("DB_PASSWORD"), # Reads DB_PASSWORD from .env
            database=config("DB_NAME")     # Reads DB_NAME from .env
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error in callback handler: {err}")
        return None

def update_order_payment_status(checkout_request_id, new_status, mpesa_receipt_number=None, transaction_date=None):
    """Updates an order's status and M-Pesa details in the database."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            if new_status == "Paid":
                cursor.execute(
                    "UPDATE orders SET status = %s, mpesa_receipt_number = %s, mpesa_transaction_date = %s WHERE checkout_request_id = %s",
                    (new_status, mpesa_receipt_number, transaction_date, checkout_request_id)
                )
            else: # For failed payments
                cursor.execute(
                    "UPDATE orders SET status = %s WHERE checkout_request_id = %s",
                    (new_status, checkout_request_id)
                )
            conn.commit()
            logger.info(f"Order {checkout_request_id} status updated to {new_status}.")
            return True
        except mysql.connector.Error as err:
            logger.error(f"Error updating order payment status for {checkout_request_id}: {err}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    return False

# ==== M-Pesa Callback Route ====
# This is the endpoint that M-Pesa's Daraja API will send payment notifications to.
# The URL for this endpoint (e.g., https://your-ngrok-url.ngrok-free.app/mpesa_callback)
# is what you set as CALLBACK_URL in your .env file, which your Streamlit app uses.
@app.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    logger.info("Received M-Pesa callback.")
    try:
        data = request.get_json()
        logger.info(f"Callback raw data: {json.dumps(data, indent=2)}")

        # Extracting relevant parts from the M-Pesa callback structure
        if 'Body' not in data or 'stkCallback' not in data['Body']:
            logger.warning("Invalid M-Pesa callback structure: Missing Body or stkCallback.")
            return jsonify({"ResultCode": 1, "ResultDesc": "Invalid callback structure"}), 400

        stk_callback = data['Body']['stkCallback']
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        merchant_request_id = stk_callback.get('MerchantRequestID')

        if not checkout_request_id or result_code is None:
            logger.warning(f"Missing essential data in callback: CheckoutRequestID={checkout_request_id}, ResultCode={result_code}")
            return jsonify({"ResultCode": 1, "ResultDesc": "Missing essential callback data"}), 400

        logger.info(f"Callback for CheckoutRequestID: {checkout_request_id}, ResultCode: {result_code}")

        if result_code == 0:
            # Payment was successful
            callback_metadata = stk_callback.get('CallbackMetadata')
            mpesa_receipt_number = None
            mpesa_transaction_date = None

            if callback_metadata and 'Item' in callback_metadata:
                for item in callback_metadata['Item']:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt_number = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        # Convert M-Pesa timestamp to datetime object
                        # Format is YYYYMMDDHHmmss
                        if item.get('Value'):
                            mpesa_transaction_date = datetime.strptime(str(item['Value']), '%Y%m%d%H%M%S')

            logger.info(f"Successful payment: MpesaReceiptNumber={mpesa_receipt_number}, TransactionDate={mpesa_transaction_date}")

            update_order_payment_status(
                checkout_request_id,
                "Paid",
                mpesa_receipt_number,
                mpesa_transaction_date
            )
            # You might want to trigger notifications or further actions here
        else:
            # Payment failed or was cancelled
            logger.warning(f"Payment failed/cancelled for CheckoutRequestID {checkout_request_id}: {result_desc}")
            update_order_payment_status(checkout_request_id, "Payment Failed")

        # M-Pesa expects a specific JSON response to acknowledge receipt of the callback
        return jsonify({"ResultCode": 0, "ResultDesc": "Callback processed successfully"}), 200

    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {e}", exc_info=True)
        return jsonify({"ResultCode": 1, "ResultDesc": "Internal server error"}), 500

if __name__ == '__main__':
    # This block runs the Flask development server.
    # It listens on all available network interfaces (0.0.0.0) on port 5000.
    # This is the port that ngrok will tunnel to.
    app.run(host='0.0.0.0', port=5000)