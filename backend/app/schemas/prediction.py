from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# Global regions (101 countries)
VALID_REGIONS = {
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu",
    "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi",
    "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun",
    "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT",
}

VALID_CROPS = {
    "Maize", "Rice", "Sorghum", "Cassava", "Wheat", "Yam", "Cowpea",
    "Groundnut", "Millet", "Sugarcane", "Tomato", "Cotton",
}

VALID_SOIL_TYPES = {
    "Loamy", "Clay", "Sandy", "Clay Loam",
    "Sandy Loam", "Silty Clay", "Peat", "Chalky",
}

VALID_SEASONS = {"Wet", "Dry", "Rabi", "Kharif"}


class PredictionRequest(BaseModel):
    crop_name: str = Field(..., examples=["Maize"])
    region: str = Field(..., examples=["Nigeria"])
    soil_type: str = Field(..., examples=["Loamy"])
    rainfall: float = Field(..., ge=0, le=5000, examples=[820.0])
    temperature: float = Field(..., ge=-10, le=60, examples=[28.5])
    humidity: float = Field(..., ge=0, le=100, examples=[65.0])
    fertilizer_usage: float = Field(..., ge=0, le=2000, examples=[120.0])
    pesticide_usage: float = Field(..., ge=0, le=500, examples=[4.5])
    area_cultivated: float = Field(..., gt=0, le=100000, examples=[3.5])
    season: str = Field(..., examples=["Wet"])
    year: int = Field(..., ge=2000, le=2100, examples=[2025])

    @field_validator("crop_name")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        if v not in VALID_CROPS:
            raise ValueError(f"'{v}' not supported. Supported: {sorted(VALID_CROPS)}")
        return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        if v not in VALID_REGIONS:
            raise ValueError(f"'{v}' not recognised.")
        return v

    @field_validator("soil_type")
    @classmethod
    def validate_soil(cls, v: str) -> str:
        if v not in VALID_SOIL_TYPES:
            raise ValueError(f"'{v}' not supported.")
        return v

    @field_validator("season")
    @classmethod
    def validate_season(cls, v: str) -> str:
        if v not in VALID_SEASONS:
            raise ValueError(f"'{v}' not valid.")
        return v


class InputSummary(BaseModel):
    crop_name: str
    region: str
    soil_type: str
    rainfall: float
    temperature: float
    humidity: float
    fertilizer_usage: float
    pesticide_usage: float
    area_cultivated: float
    season: str
    year: int


class PredictionResponse(BaseModel):
    prediction_id: int
    predicted_yield: float
    yield_unit: str = "tons/ha"
    confidence_score: Optional[float] = None
    model_used: str
    interpretation: str
    input_summary: InputSummary
    timestamp: datetime
    status: str = "success"


# ----- Records used by the history endpoints -----------------
class PredictionRecord(BaseModel):
    model_config = {
        "from_attributes": True,
    }

    id: int
    user_id: Optional[int] = None
    crop_name: str
    region: str
    soil_type: str
    rainfall: float
    temperature: float
    humidity: float
    fertilizer_usage: float
    pesticide_usage: float
    area_cultivated: float
    season: str
    year: int
    predicted_yield: float
    yield_unit: str
    confidence_score: Optional[float] = None
    model_used: str
    status: str
    notes: Optional[str] = None
    created_at: datetime


class PredictionList(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[PredictionRecord]