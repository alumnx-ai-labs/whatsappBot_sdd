from pydantic import BaseModel, ConfigDict, Field


class MetadataInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    business_name: str = Field(alias="businessName", min_length=1)
    contact_person: str = Field(alias="contactPerson", min_length=1)
    whatsapp_phone: str = Field(alias="whatsappPhone", min_length=1)
    address: str | None = None
    sector: str | None = None
    business_description: str | None = Field(default=None, alias="businessDescription")


class MetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    business_name: str = Field(alias="businessName")
    contact_person: str = Field(alias="contactPerson")
    whatsapp_phone: str = Field(alias="whatsappPhone")
    address: str | None
    sector: str | None
    business_description: str | None = Field(alias="businessDescription")
    source_type: str = Field(alias="sourceType")
