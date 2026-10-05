from .main import app
from .routers.scoring import router as scoring_router

app.include_router(scoring_router)
app.version = "0.8.0"
