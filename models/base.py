"""Base model class providing common functionality for all models.
"""

from database import db
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, event, Boolean, String, ForeignKey  # Added ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship  # Added relationship import

class BaseModel(db.Model):
    """Abstract base model class that provides common functionality."""
    
    __abstract__ = True

    # Primary key for all models
    id = Column(Integer, primary_key=True)

    # Timestamps for all models
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls):
        """Generate table name automatically from class name."""
        return cls.__name__.lower() + 's'

    def save(self):
        """Save the model instance."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the model instance."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        """Update model instance attributes."""
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)
        return self.save()

    @classmethod
    def create(cls, **kwargs):
        """Create a new model instance."""
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def get_by_id(cls, id):
        """Get model instance by ID."""
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """Get all model instances."""
        return cls.query.all()

    def to_dict(self):
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def from_dict(self, data):
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def __repr__(self):
        """String representation of model instance."""
        return f'<{self.__class__.__name__} {self.id}>'

# Event listeners for automatic timestamps
@event.listens_for(BaseModel, 'before_insert', propagate=True)
def set_created_at(mapper, connection, target):
    """Set created_at timestamp before insert."""
    target.created_at = datetime.utcnow()
    target.updated_at = datetime.utcnow()

@event.listens_for(BaseModel, 'before_update', propagate=True)
def set_updated_at(mapper, connection, target):
    """Set updated_at timestamp before update."""
    target.updated_at = datetime.utcnow()

class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""
    
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        """Soft delete the model instance."""
        self.deleted_at = datetime.utcnow()
        return self.save()

    def restore(self):
        """Restore a soft-deleted model instance."""
        self.deleted_at = None
        return self.save()

    @property
    def is_deleted(self):
        """Check if model instance is soft-deleted."""
        return self.deleted_at is not None

class TimestampMixin:
    """Mixin to add additional timestamp functionality."""
    
    last_accessed_at = Column(DateTime, nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    def touch(self):
        """Update last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()
        return self.save()

    def mark_modified(self):
        """Update last modified timestamp."""
        self.last_modified_at = datetime.utcnow()
        return self.save()

class VersionMixin:
    """Mixin to add versioning functionality."""
    
    version = Column(Integer, default=1, nullable=False)

    def increment_version(self):
        """Increment version number."""
        self.version += 1
        return self.save()

    @property
    def is_latest_version(self):
        """Check if this is the latest version."""
        latest = self.__class__.query.filter_by(
            id=self.id
        ).order_by(
            self.__class__.version.desc()
        ).first()
        return latest.version == self.version

class StatusMixin:
    """Mixin to add status functionality."""
    
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default='active', nullable=False)

    def activate(self):
        """Activate the model instance."""
        self.is_active = True
        self.status = 'active'
        return self.save()

    def deactivate(self):
        """Deactivate the model instance."""
        self.is_active = False
        self.status = 'inactive'
        return self.save()

    @property
    def is_enabled(self):
        """Check if model instance is active."""
        return self.is_active and self.status == 'active'

class AuditMixin:
    """Mixin to add audit functionality."""
    
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    @declared_attr
    def created_by(cls):
        """Relationship to user who created the instance."""
        return relationship('User', foreign_keys=[cls.created_by_id])

    @declared_attr
    def updated_by(cls):
        """Relationship to user who last updated the instance."""
        return relationship('User', foreign_keys=[cls.updated_by_id])

    def set_created_by(self, user):
        """Set user who created the instance."""
        self.created_by_id = user.id if user else None
        return self.save()

    def set_updated_by(self, user):
        """Set user who updated the instance."""
        self.updated_by_id = user.id if user else None
        return self.save()
