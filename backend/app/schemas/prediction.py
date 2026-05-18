from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# Global regions (101 countries)
VALID_REGIONS = {
    "Albania", "Algeria", "Angola", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Belarus",
    "Belgium", "Botswana", "Brazil", "Bulgaria", "Burkina Faso", "Burundi",
    "Cameroon", "Canada", "Chad", "China", "Colombia", "Congo",
    "Costa Rica", "Croatia", "Cyprus", "Czech Republic", "Denmark",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Eritrea",
    "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia",
    "Georgia", "Germany", "Ghana", "Greece", "Guatemala", "Guinea",
    "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland",
    "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy",
    "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Korea", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia",
    "Libya", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia",
    "Mali", "Malta", "Mauritania", "Mauritius", "Mexico", "Moldova",
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria",
    "Norway", "Oman", "Pakistan", "Panama", "Papua New Guinea", "Paraguay",
    "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
    "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", "Sierra Leone",
    "Singapore", "Slovakia", "Slovenia", "Somalia", "South Africa",
    "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden",
    "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand",
    "Timor-Leste", "Togo", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Venezuela",
    "Vietnam", "Yemen", "Zambia", "Zimbabwe",
}

VALID_CROPS = {
    "Maize", "Rice", "Wheat", "Cassava", "Yams", "Sorghum",
    "Potatoes", "Soybeans", "Sweet potatoes", "Plantains",
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