from database.hub import hub
from engine.hydroma.biofertilizer.models import NojinMaterial, NojinSoilType

with hub.get_session() as session:
    print('Materials:', session.query(NojinMaterial).count())
    print('Soils:', session.query(NojinSoilType).count())
