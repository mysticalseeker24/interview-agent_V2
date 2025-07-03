"""Database service for transcription operations."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.models.transcription import Transcription
from app.models.media_device import MediaDevice
from app.schemas.transcription import TranscriptionRead, TranscriptionStatus

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations related to transcriptions."""
    
    def __init__(self, db: AsyncSession):
        """Initialize Database Service."""
        self.db = db
    
    async def create_transcription_record(
        self,
        user_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        session_id: Optional[int] = None
    ) -> Transcription:
        """
        Create a new transcription record.
        
        Args:
            user_id: User ID
            filename: Original filename
            file_path: Saved file path
            file_size: File size in bytes
            file_type: File type/extension
            session_id: Optional interview session ID
            
        Returns:
            Created transcription record
        """
        transcription = Transcription(
            user_id=user_id,
            session_id=session_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            status="pending"
        )
        
        self.db.add(transcription)
        await self.db.flush()  # Get ID
        await self.db.commit()
        
        logger.info(f"Created transcription record {transcription.id}")
        return transcription
    
    async def update_transcription_result(
        self,
        transcription_id: int,
        transcript_text: str,
        segments: List[Dict[str, Any]],
        provider: str,
        model_used: str,
        confidence_score: float,
        fallback_used: bool = False,
        duration_seconds: Optional[float] = None
    ) -> Optional[Transcription]:
        """
        Update transcription with results.
        
        Args:
            transcription_id: Transcription ID
            transcript_text: Full transcript text
            segments: Transcription segments
            provider: Provider used (openai, assemblyai)
            model_used: Model used
            confidence_score: Overall confidence score
            fallback_used: Whether fallback was used
            duration_seconds: Audio duration
            
        Returns:
            Updated transcription record or None
        """
        result = await self.db.execute(
            select(Transcription).where(Transcription.id == transcription_id)
        )
        transcription = result.scalar_one_or_none()
        
        if transcription:
            transcription.transcript_text = transcript_text
            transcription.segments = segments
            transcription.provider = provider
            transcription.model_used = model_used
            transcription.confidence_score = confidence_score
            transcription.fallback_used = 1 if fallback_used else 0
            transcription.duration_seconds = duration_seconds
            transcription.status = "completed"
            transcription.completed_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Updated transcription {transcription_id} with results")
            return transcription
        
        return None
    
    async def update_transcription_error(
        self,
        transcription_id: int,
        error_message: str
    ) -> Optional[Transcription]:
        """
        Update transcription with error.
        
        Args:
            transcription_id: Transcription ID
            error_message: Error message
            
        Returns:
            Updated transcription record or None
        """
        result = await self.db.execute(
            select(Transcription).where(Transcription.id == transcription_id)
        )
        transcription = result.scalar_one_or_none()
        
        if transcription:
            transcription.status = "failed"
            transcription.processing_error = error_message
            transcription.completed_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Updated transcription {transcription_id} with error")
            return transcription
        
        return None
    
    async def get_transcription_by_id(
        self,
        transcription_id: int,
        user_id: int
    ) -> Optional[TranscriptionRead]:
        """
        Get transcription by ID for specific user.
        
        Args:
            transcription_id: Transcription ID
            user_id: User ID
            
        Returns:
            Transcription data or None
        """
        result = await self.db.execute(
            select(Transcription).where(
                Transcription.id == transcription_id,
                Transcription.user_id == user_id
            )
        )
        transcription = result.scalar_one_or_none()
        
        if transcription:
            return TranscriptionRead.from_orm(transcription)
        return None
    
    async def get_transcription_status(
        self,
        transcription_id: int,
        user_id: int
    ) -> Optional[TranscriptionStatus]:
        """
        Get transcription status by ID.
        
        Args:
            transcription_id: Transcription ID
            user_id: User ID
            
        Returns:
            Transcription status or None
        """
        result = await self.db.execute(
            select(Transcription).where(
                Transcription.id == transcription_id,
                Transcription.user_id == user_id
            )
        )
        transcription = result.scalar_one_or_none()
        
        if transcription:
            return TranscriptionStatus(
                id=transcription.id,
                status=transcription.status,
                transcript=transcription.transcript_text,
                confidence_score=transcription.confidence_score,
                provider=transcription.provider,
                fallback_used=bool(transcription.fallback_used),
                created_at=transcription.created_at,
                completed_at=transcription.completed_at,
                error=transcription.processing_error
            )
        return None
    
    async def list_user_transcriptions(self, user_id: int) -> List[TranscriptionRead]:
        """
        List all transcriptions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user transcriptions
        """
        result = await self.db.execute(
            select(Transcription).where(Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
        )
        transcriptions = result.scalars().all()
        
        return [TranscriptionRead.from_orm(t) for t in transcriptions]
    
    async def save_media_devices(
        self,
        user_id: int,
        devices: List[Dict[str, Any]]
    ) -> List[MediaDevice]:
        """
        Save detected media devices for user.
        
        Args:
            user_id: User ID
            devices: List of device information
            
        Returns:
            List of saved device records
        """
        # Clear existing devices for user
        await self.db.execute(
            select(MediaDevice).where(MediaDevice.user_id == user_id)
        )
        
        saved_devices = []
        for device_info in devices:
            device = MediaDevice(
                user_id=user_id,
                device_id=device_info.get('device_id'),
                device_name=device_info.get('device_name'),
                device_type=device_info.get('device_type'),
                capabilities=device_info.get('capabilities'),
                is_default=device_info.get('is_default', False),
                is_available=device_info.get('is_available', True)
            )
            
            self.db.add(device)
            saved_devices.append(device)
        
        await self.db.commit()
        logger.info(f"Saved {len(saved_devices)} devices for user {user_id}")
        return saved_devices
    
    async def create_transcription(
        self,
        user_id: int,
        filename: str,
        transcript: str,
        segments: List[Dict[str, Any]],
        confidence: float,
        language: str,
        provider: str,
        db: Session
    ) -> Transcription:
        """
        Create a new transcription record with completed data.
        
        Args:
            user_id: User ID
            filename: Original filename
            transcript: Transcribed text
            segments: Transcription segments
            confidence: Confidence score
            language: Language code
            provider: Provider used (openai/assemblyai)
            db: Database session
            
        Returns:
            Created transcription record
        """
        try:
            transcription = Transcription(
                user_id=user_id,
                filename=filename,
                transcript_text=transcript,
                segments=segments,
                confidence_score=confidence,
                language=language,
                provider=provider,
                status="completed",
                file_type="audio",
                file_size=0,  # Will be updated if needed
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            db.add(transcription)
            db.commit()
            db.refresh(transcription)
            
            logger.info(f"Created transcription record: {transcription.id}")
            return transcription
            
        except Exception as e:
            logger.error(f"Error creating transcription: {str(e)}")
            db.rollback()
            raise

    async def get_user_transcriptions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        db: Session = None
    ) -> List[Transcription]:
        """
        Get all transcriptions for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Database session
            
        Returns:
            List of transcription records
        """
        try:
            query = db.query(Transcription).filter(
                Transcription.user_id == user_id
            ).order_by(Transcription.created_at.desc())
            
            transcriptions = query.offset(skip).limit(limit).all()
            
            logger.info(f"Retrieved {len(transcriptions)} transcriptions for user {user_id}")
            return transcriptions
            
        except Exception as e:
            logger.error(f"Error fetching transcriptions: {str(e)}")
            raise

    async def get_user_transcriptions_count(
        self,
        user_id: int,
        db: Session = None
    ) -> int:
        """
        Get total count of transcriptions for a user.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Total count of transcriptions
        """
        try:
            count = db.query(Transcription).filter(
                Transcription.user_id == user_id
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting transcriptions: {str(e)}")
            raise

    async def get_transcription(
        self,
        transcription_id: int,
        user_id: int,
        db: Session = None
    ) -> Optional[Transcription]:
        """
        Get a specific transcription by ID and user.
        
        Args:
            transcription_id: Transcription ID
            user_id: User ID
            db: Database session
            
        Returns:
            Transcription record or None if not found
        """
        try:
            transcription = db.query(Transcription).filter(
                Transcription.id == transcription_id,
                Transcription.user_id == user_id
            ).first()
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error fetching transcription {transcription_id}: {str(e)}")
            raise

    async def delete_transcription(
        self,
        transcription_id: int,
        user_id: int,
        db: Session = None
    ) -> bool:
        """
        Delete a transcription by ID and user.
        
        Args:
            transcription_id: Transcription ID
            user_id: User ID
            db: Database session
            
        Returns:
            True if deleted, False if not found
        """
        try:
            transcription = db.query(Transcription).filter(
                Transcription.id == transcription_id,
                Transcription.user_id == user_id
            ).first()
            
            if transcription:
                db.delete(transcription)
                db.commit()
                logger.info(f"Deleted transcription {transcription_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting transcription {transcription_id}: {str(e)}")
            db.rollback()
            raise

    async def update_user_devices(
        self,
        user_id: int,
        devices: List[Dict[str, Any]],
        db: Session = None
    ) -> None:
        """
        Update user's media devices in the database.
        
        Args:
            user_id: User ID
            devices: List of device information
            db: Database session
        """
        try:
            # Remove existing devices for this user
            db.query(MediaDevice).filter(
                MediaDevice.user_id == user_id
            ).delete()
            
            # Add new devices
            for device in devices:
                device_record = MediaDevice(
                    user_id=user_id,
                    device_id=device["id"],
                    device_name=device["label"],
                    device_type=device["device_type"],
                    capabilities=device["capabilities"],
                    is_default=device["is_default"],
                    is_available=True,
                    detected_at=datetime.utcnow()
                )
                db.add(device_record)
            
            db.commit()
            logger.info(f"Updated {len(devices)} devices for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user devices: {str(e)}")
            db.rollback()
            raise
