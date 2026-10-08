from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    Food, FoodNutrient, Nutrient, SafetyEvidenceRecord,
    TraceEventRecord, FeedbackRecordEntity, KnowledgeEntityRecord,
    KnowledgeRelationRecord, EvaluationRunRecord,
)

class PersistentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, entity):
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, model, entity_id: str):
        return await self.session.get(model, entity_id)

    async def list_by(self, model, field, value, limit: int = 100):
        result = await self.session.execute(
            select(model).where(field == value).limit(limit)
        )
        return list(result.scalars().all())

    async def commit(self):
        await self.session.commit()

class NutritionRepository(PersistentRepository):
    async def find_foods(self, name: str, limit: int = 20):
        result = await self.session.execute(
            select(Food).where(Food.name.ilike(f"%{name}%")).limit(limit)
        )
        return list(result.scalars().all())

    async def nutrients_for_food(self, food_id: str):
        result = await self.session.execute(
            select(FoodNutrient, Nutrient)
            .join(Nutrient, FoodNutrient.nutrient_id == Nutrient.id)
            .where(FoodNutrient.food_id == food_id)
        )
        return list(result.all())

class KnowledgeRepository(PersistentRepository):
    async def neighbors(self, entity_id: str):
        result = await self.session.execute(
            select(KnowledgeRelationRecord).where(
                (KnowledgeRelationRecord.subject_id == entity_id) |
                (KnowledgeRelationRecord.object_id == entity_id)
            )
        )
        return list(result.scalars().all())

class TraceRepository(PersistentRepository):
    async def history(self, subject_id: str, limit: int = 100):
        result = await self.session.execute(
            select(TraceEventRecord)
            .where(TraceEventRecord.subject_id == subject_id)
            .order_by(TraceEventRecord.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

class FeedbackRepository(PersistentRepository):
    async def for_subject(self, subject_id: str, limit: int = 100):
        result = await self.session.execute(
            select(FeedbackRecordEntity)
            .where(FeedbackRecordEntity.subject_id == subject_id)
            .order_by(FeedbackRecordEntity.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
