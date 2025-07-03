"""
Vector Sync Service for continuous synchronization of question embeddings.
Listens to PostgreSQL triggers via RabbitMQ and updates Pinecone vectors.
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class VectorSyncService:
    """Service for continuous synchronization between PostgreSQL and Pinecone."""
    
    def __init__(self):
        """Initialize the vector sync service."""
        self.embedding_service = EmbeddingService()
        self.rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
        self.exchange_name = 'questions_events'
        self.queue_name = 'vector_sync_queue'
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        logger.info("Vector sync service initialized")
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            # Bind queue to exchange with routing keys
            await self.queue.bind(self.exchange, routing_key='questions.created')
            await self.queue.bind(self.exchange, routing_key='questions.updated')
            
            logger.info("Connected to RabbitMQ successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    async def process_message(self, message: aio_pika.IncomingMessage):
        """
        Process incoming message from RabbitMQ.
        
        Args:
            message: IncomingMessage object from RabbitMQ
        """
        async with message.process():
            try:
                # Decode message body
                body = json.loads(message.body.decode())
                routing_key = message.routing_key
                
                logger.info(f"Received message with routing key: {routing_key}")
                
                if routing_key == 'questions.created':
                    await self.handle_question_created(body)
                elif routing_key == 'questions.updated':
                    await self.handle_question_updated(body)
                else:
                    logger.warning(f"Unknown routing key: {routing_key}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
    
    async def handle_question_created(self, data: Dict[str, Any]):
        """
        Handle question created event.
        
        Args:
            data: Question data from event
        """
        try:
            question_id = data.get('id')
            logger.info(f"Processing question created event for question {question_id}")
            
            # Sync to Pinecone
            await self.embedding_service.sync_question_on_create(data)
            
        except Exception as e:
            logger.error(f"Error handling question created event: {str(e)}")
    
    async def handle_question_updated(self, data: Dict[str, Any]):
        """
        Handle question updated event.
        
        Args:
            data: Question data from event
        """
        try:
            question_id = data.get('id')
            logger.info(f"Processing question updated event for question {question_id}")
            
            # Sync to Pinecone
            await self.embedding_service.sync_question_on_update(data)
            
        except Exception as e:
            logger.error(f"Error handling question updated event: {str(e)}")
    
    async def start_listening(self):
        """Start listening for messages from RabbitMQ."""
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            
            async def on_message(message: aio_pika.IncomingMessage):
                await self.process_message(message)
            
            # Start consuming messages
            await self.queue.consume(on_message)
            
            logger.info(f"Started listening on queue: {self.queue_name}")
            
            # Keep service running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
                
        except Exception as e:
            logger.error(f"Error in message listener: {str(e)}")
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
    
    async def publish_event(self, routing_key: str, data: Dict[str, Any]):
        """
        Publish event to RabbitMQ.
        
        Args:
            routing_key: Routing key for the message
            data: Event data to publish
        """
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            
            message = aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await self.exchange.publish(
                message, 
                routing_key=routing_key
            )
            
            logger.info(f"Published event with routing key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")
    
    async def close(self):
        """Close connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Closed connection to RabbitMQ")
