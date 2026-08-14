from fastapi import APIRouter
from schemas import DerivedIndicatorsResponse, ContextSignalSchema, ProvenanceTag

router = APIRouter(prefix="/context", tags=["Module 3: Problem Detection & Context"])

@router.get("/{geography_id}/signals", response_model=DerivedIndicatorsResponse)
def get_context_signals(geography_id: str):
    signals = [
        ContextSignalSchema(
            id="SIG-001",
            title="Surface Hydrologic Deficit & Moisture Stress Proxy",
            domain="Water",
            severity="ELEVATED",
            description="Satellite moisture deficit index indicates elevated pre-monsoon hydrologic stress across local basalt soil formations.",
            underlying_data_citation="Sentinel-2 L2A Band Ratio Moisture Proxy Model",
            provenance_tag=ProvenanceTag.MODELLED_SATELLITE_PROXY,
            affected_villages_count=18,
            measurement_type="proxy",
            direct_measurement=False,
            source="Sentinel-2 spectral indices",
            limitations="Does not directly measure groundwater storage or aquifer depth; regional moisture deficit proxy."
        ),
        ContextSignalSchema(
            id="SIG-002",
            title="Agricultural Canopy Water Stress",
            domain="Agriculture",
            severity="MODERATE",
            description="NDVI index dropped below 0.35 threshold in un-irrigated block sectors.",
            underlying_data_citation="Sentinel-2 L2A Scene Band 8/4 Derived NDVI",
            provenance_tag=ProvenanceTag.MODELLED_SATELLITE_PROXY,
            affected_villages_count=32,
            measurement_type="proxy",
            direct_measurement=False,
            source="Sentinel-2 spectral indices",
            limitations="Canopy vegetation proxy index."
        ),
        ContextSignalSchema(
            id="SIG-003",
            title="Surface Water Turbidity & Spectral Variance Anomaly Zone",
            domain="Wastewater",
            severity="CRITICAL",
            description="Elevated SWIR/Red reflectance variance detected near river drainage points, indicating suspended solids & turbidity elevation.",
            underlying_data_citation="Sentinel-2 Turbidity Proxy (Band 4 Red Reflectance Variance)",
            provenance_tag=ProvenanceTag.MODELLED_SATELLITE_PROXY,
            affected_villages_count=12,
            measurement_type="proxy",
            direct_measurement=False,
            source="Sentinel-2 spectral indices",
            limitations="Spectral anomaly does not establish chemical contamination, pathogen presence, toxicity, or municipal effluent attribution."
        )
    ]

    return DerivedIndicatorsResponse(
        geography_id=geography_id,
        water_stress_index=0.74,
        vegetation_condition_index=0.68,
        flood_risk_score=0.32,
        groundwater_drawdown_rate_m_yr=-1.2,
        signals=signals
    )
