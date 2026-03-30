from app.infra.settings import Settings


def test_is_production_true_for_production_aliases() -> None:
    prod_settings = Settings.model_construct(environment='production')
    short_prod_settings = Settings.model_construct(environment='prod')

    assert prod_settings.is_production is True
    assert short_prod_settings.is_production is True


def test_is_production_false_for_non_production_environment() -> None:
    dev_settings = Settings.model_construct(environment='development')
    assert dev_settings.is_production is False
