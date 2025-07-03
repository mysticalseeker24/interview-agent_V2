"""
Database event listener for TalentSync Interview Service.
This script listens for PostgreSQL notifications and sends them to RabbitMQ.
"""

import os
import sys
import json
import logging
import asyncio
import signal
import psycopg2
import psycopg2.extensions
import aio_pika
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("db_listener")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/talentsync")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
EXCHANGE_NAME = "questions_events"
CHANNEL_NAME = "question_changes"

# Global variables
conn = None
rabbitmq_connection = None
rabbitmq_channel = None
rabbitmq_exchange = None
should_exit = False


async def setup_rabbitmq():
    """Set up RabbitMQ connection and exchange."""
    global rabbitmq_connection, rabbitmq_channel, rabbitmq_exchange
    
    try:
        # Connect to RabbitMQ
        rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
        rabbitmq_channel = await rabbitmq_connection.channel()
        
        # Declare exchange
        rabbitmq_exchange = await rabbitmq_channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        logger.info("Connected to RabbitMQ successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        sys.exit(1)


async def publish_event(routing_key, payload):
    """Publish event to RabbitMQ."""
    try:
        # Convert payload to JSON string
        message_body = json.dumps(payload).encode()
        
        # Create message
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            timestamp=datetime.utcnow().timestamp()
        )
        
        # Publish message
        await rabbitmq_exchange.publish(message, routing_key=routing_key)
        
        logger.info(f"Published event with routing key '{routing_key}'")
        
    except Exception as e:
        logger.error(f"Failed to publish event: {str(e)}")


async def process_notification(notification):
    """Process PostgreSQL notification."""
    try:
        # Parse notification payload
        payload = json.loads(notification.payload)
        table = payload.get('table')
        action = payload.get('action')
        data = payload.get('data', {})
        
        # Skip if not questions table
        if table != 'questions':
            return
            
        # Determine routing key
        routing_key = None
        if action == 'INSERT':
            routing_key = 'questions.created'
        elif action == 'UPDATE':
            routing_key = 'questions.updated'
        else:
            logger.warning(f"Unsupported action: {action}")
            return
            
        # Publish event to RabbitMQ
        await publish_event(routing_key, data)
        
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")


def handle_postgres_notification(conn, notify):
    """Handle PostgreSQL notification in main event loop."""
    conn.poll()
    
    while conn.notifies:
        notification = conn.notifies.pop(0)
        logger.info(f"Received notification on channel {notification.channel}")
        
        # Schedule async processing of notification
        asyncio.create_task(process_notification(notification))


async def listen_postgresql_events():
    """Listen for PostgreSQL events."""
    global conn, should_exit
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create cursor
        cursor = conn.cursor()
        
        # Listen for notifications
        cursor.execute(f"LISTEN {CHANNEL_NAME};")
        
        logger.info(f"Listening for PostgreSQL notifications on channel: {CHANNEL_NAME}")
        
        # Set up file descriptor for Postgres connection
        pg_fd = conn.fileno()
        pg_loop = asyncio.get_event_loop()
        
        # Add reader to event loop
        pg_loop.add_reader(pg_fd, handle_postgres_notification, conn, None)
        
        # Keep running until should_exit is True
        while not should_exit:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in PostgreSQL listener: {str(e)}")
        
    finally:
        # Clean up
        if conn:
            if pg_fd and pg_loop:
                pg_loop.remove_reader(pg_fd)
            conn.close()


def signal_handler(sig, frame):
    """Handle termination signals."""
    global should_exit
    
    logger.info(f"Received signal {sig}, shutting down...")
    should_exit = True


async def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup RabbitMQ
    await setup_rabbitmq()
    
    # Start PostgreSQL listener
    await listen_postgresql_events()
    
    # Clean up
    if rabbitmq_connection:
        await rabbitmq_connection.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)
