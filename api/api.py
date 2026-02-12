from fastapi import APIRouter

from api.routers import auth, users, assets, datasets, models, training, predictions, feedback, simulation, intelligence, admin, inspections, metadata

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(training.router, prefix="/train", tags=["training"])
api_router.include_router(predictions.router, prefix="/predict", tags=["predictions"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["inspections"])
api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
