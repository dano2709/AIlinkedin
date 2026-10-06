from .main_phase8 import app
from .routers.notifications import router as notifications_router

app.include_router(notifications_router)
app.version = "0.9.0"
