from app.core.config import settings
from app.core.redis import rediss
from app.schemas.NotificationsSchema import NotificationSchema


async def send_notification(notification: NotificationSchema):
    await rediss.publish(settings.REDIS_NOTIFICATIONS_CHANNEL, notification.model_dump_json())
