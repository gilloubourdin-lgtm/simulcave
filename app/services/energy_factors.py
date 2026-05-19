# app/services/energy_factors.py

ENERGY_PRICE_CHF_PER_KWH = {
    "electricity": 0.24,
    "heat_pump": 0.18,
    "gas": 0.16,
    "oil": 0.19,
}

CO2_FACTOR_KG_PER_KWH = {
    "electricity": 0.09,
    "heat_pump": 0.04,
    "gas": 0.23,
    "oil": 0.30,
}


def get_energy_price(source: str = "electricity") -> float:
    return ENERGY_PRICE_CHF_PER_KWH.get(source, 0.24)


def get_co2_factor(source: str = "electricity") -> float:
    return CO2_FACTOR_KG_PER_KWH.get(source, 0.09)