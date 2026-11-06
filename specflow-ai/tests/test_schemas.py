from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from specflow.config import MODEL_REGISTRY, Settings, compute_cost, get_model_profile
from specflow.normalization import (
    expand_designations,
    normalize_designation,
    parse_contacts,
    parse_poles,
    parse_trip_curve,
    value_in_unit,
)
from specflow.schemas import (
    CatalogItem,
    ComponentCategory,
    EngineeringItem,
    EstimateLine,
    EstimateSettings,
    EstimateTotals,
    ExtractedRawBOM,
    LaborAssessment,
    LLMCallRecord,
    MatchBatchResult,
    MatchResult,
    MatchType,
    PipelineRun,
    PipelineStage,
    PricedItem,
    SpecKey,
    TechnicalParameter,
    TechnicalSpecs,
    TokenUsage,
    UnitOfMeasure,
    ValidatorReview,
    VisionPageExtraction,
)

# --- нормализация -------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("QF1-QF3, QF5", ["QF1", "QF2", "QF3", "QF5"]),
        ("QF1…QF3", ["QF1", "QF2", "QF3"]),
        ("QF1⋯QF3", ["QF1", "QF2", "QF3"]),
        ("QF1...3", ["QF1", "QF2", "QF3"]),
        ("XT1:1-4", ["XT1:1", "XT1:2", "XT1:3", "XT1:4"]),
        ("KM1.1÷KM1.3", ["KM1.1", "KM1.2", "KM1.3"]),
        ("-QF7", ["QF7"]),
        ("=A1+B2-QF3", ["QF3"]),
        ("КМ1; км2", ["KM1", "KM2"]),  # кириллица -> латиница
        ("QF1-KM3", ["QF1", "KM3"]),  # разные буквенные коды — не диапазон
        ("QF5-QF2", ["QF5-QF2"]),  # убывающий — не раскрываем
        ("", []),
    ],
)
def test_expand_designations(raw, expected):
    assert expand_designations(raw) == expected


def test_normalize_designation_homoglyphs():
    assert normalize_designation(" ХТ1 ") == "XT1"
    assert normalize_designation("НL2") == "HL2"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("3P+N", (3, True)), ("1П+Н", (1, True)), ("4P", (4, False)), ("2", (2, False)),
     ("16A 3P", (3, False)), ("2-полюсный", (2, False)), ("7P", (None, False))],
)
def test_parse_poles(value, expected):
    assert parse_poles(value) == expected


def test_parse_misc():
    assert parse_trip_curve("C16") == "C"
    assert parse_trip_curve("хар. D") == "D"
    assert parse_trip_curve("AC-3") is None
    assert parse_contacts("1NO+1NC") == (1, 1)
    assert parse_contacts("2З+1Р") == (2, 1)
    assert value_in_unit("0,4 кВ", "", "V") == pytest.approx(400)
    assert value_in_unit("230/400", "В", "V", prefer_max=True) == pytest.approx(400)
    assert value_in_unit("24VDC", "", "V") == pytest.approx(24)
    assert value_in_unit("30", "мА", "mA") == pytest.approx(30)


# --- технические характеристики -------------------------------------------------


def _p(key: SpecKey, value: str, unit: str = "", name: str = "") -> TechnicalParameter:
    return TechnicalParameter(key=key, name=name, value=value, unit=unit)


def test_breaker_specs_from_parameters():
    specs = TechnicalSpecs.from_parameters(
        [
            _p(SpecKey.RATED_CURRENT, "16", "А", "Iн"),
            _p(SpecKey.TRIP_CURVE, "C"),
            _p(SpecKey.POLES, "3P+N"),
            _p(SpecKey.BREAKING_CAPACITY, "4,5", "кА", "Icu"),
            _p(SpecKey.RATED_VOLTAGE, "230/400", "В"),
        ]
    )
    assert specs.rated_current_a == 16
    assert specs.trip_curve == "C"
    assert (specs.poles, specs.has_neutral) == (3, True)
    assert specs.breaking_capacity_ka == pytest.approx(4.5)
    assert specs.rated_voltage_v == 400
    text = specs.to_search_text()
    for token in ("C16", "16A", "3P+N", "4.5kA", "400V"):
        assert token in text


def test_unit_heuristics_and_cable():
    specs = TechnicalSpecs.from_parameters(
        [
            _p(SpecKey.RESIDUAL_CURRENT, "0,03"),
            _p(SpecKey.BREAKING_CAPACITY, "6000"),
            _p(SpecKey.CROSS_SECTION, "5х10"),
            _p(SpecKey.COIL_VOLTAGE, "24", "VDC"),
            _p(SpecKey.IP_RATING, "ІР 54"),
            _p(SpecKey.RATED_POWER, "750", "Вт"),
        ]
    )
    assert specs.residual_current_ma == pytest.approx(30)
    assert specs.breaking_capacity_ka == pytest.approx(6)
    assert (specs.cores_count, specs.cross_section_mm2) == (5, 10)
    assert (specs.coil_voltage_v, specs.coil_current_type) == (24, "DC")
    assert specs.ip_rating == "IP54"
    assert specs.rated_power_kw == pytest.approx(0.75)


def test_invalid_parameters_go_to_other():
    params = [_p(SpecKey.POLES, "7P"), _p(SpecKey.TRIP_CURVE, "X"), _p(SpecKey.OTHER, "сухие", name="Контакты")]
    specs = TechnicalSpecs.from_parameters(params)
    assert specs.poles is None and specs.trip_curve is None
    assert len(specs.other) == 3


def test_specs_merge_and_conflicts():
    a = TechnicalSpecs(rated_current_a=16, poles=3)
    b = TechnicalSpecs(rated_current_a=20, trip_curve="C", breaking_capacity_ka=6)
    assert a.conflicts_with(b) == ["rated_current_a"]
    merged = a.merged_with(b)
    assert merged.rated_current_a == 16 and merged.trip_curve == "C" and merged.breaking_capacity_ka == 6


# --- Агент 1: контракт и сборка BOM ---------------------------------------------


LLM_PAGE_JSON: dict[str, Any] = {
    "sheet": {
        "drawing_type": "single_line_diagram",
        "document_code": "12-24-ЭМ",
        "sheet_title": "Щит ЩР-1. Схема однолинейная",
        "sheet_number": "1",
        "total_sheets": "3",
        "revision": "",
        "organization": "",
    },
    "page_summary": "Однолинейная схема ЩР-1, ввод 63 А, 6 групп освещения.",
    "components": [
        {
            "designation": "QF1…QF6",
            "category": "circuit_breaker",
            "name": "Выключатель автоматический",
            "type_designation": "ВА47-29",
            "manufacturer": "IEK",
            "article": "",
            "parameters": [
                {"key": "rated_current", "name": "Iн", "value": "16", "unit": "А"},
                {"key": "trip_curve", "name": "", "value": "C", "unit": ""},
                {"key": "poles", "name": "", "value": "1P", "unit": ""},
            ],
            "quantity": 0,
            "unit": "pcs",
            "quantity_basis": "counted",
            "source_kind": "schematic",
            "tile_ids": ["p001_r0_c0", "p001_r0_c1"],
            "evidence": "QF1…QF6 ВА47-29 C16",
            "readability": "clear",
            "confidence": 95,
            "notes": "",
        }
    ],
    "unreadable_regions": [
        {"tile_id": "p001_r1_c2", "description": "Номинал QF7 перекрыт выноской",
         "suspected_content": "C25", "impact": "warning"}
    ],
    "cross_references": ["см. лист 2"],
    "extraction_notes": "",
}


def test_vision_contract_to_bom():
    extraction = VisionPageExtraction.model_validate(LLM_PAGE_JSON)
    assert extraction.components[0].confidence == pytest.approx(0.95)  # 95 -> 0.95

    bom = ExtractedRawBOM(run_id="test")
    created = bom.add_page_result(document_id="doc1", page_number=1, extraction=extraction, file_name="a.pdf")
    comp = created[0]
    assert comp.tags == ["QF1", "QF2", "QF3", "QF4", "QF5", "QF6"]
    assert comp.quantity == 6  # количество 0 восстановлено по раскрытым тегам
    assert comp.article is None  # пустая строка -> None
    assert comp.specs.rated_current_a == 16 and comp.specs.poles == 1
    assert comp.page_numbers == [1]
    assert bom.find_by_tag("qf4") == [comp]
    assert bom.category_counts == {"circuit_breaker": 1}
    assert bom.unreadable_regions[0].page_number == 1

    item = EngineeringItem.from_extracted(comp)
    assert item.display_designation == "QF1…QF6"
    assert not item.needs_review


def test_vision_contract_rejects_extra_fields():
    data = {**LLM_PAGE_JSON, "unexpected": 1}
    with pytest.raises(ValidationError):
        VisionPageExtraction.model_validate(data)


# --- правила Structured Outputs для всех контрактов LLM --------------------------


def _walk_objects(schema: dict[str, Any]):
    stack = [schema, *schema.get("$defs", {}).values()]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("type") == "object" or "properties" in node:
                yield node
            for key, value in node.items():
                if key != "$defs":
                    stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)


@pytest.mark.parametrize("model", [VisionPageExtraction, ValidatorReview, MatchBatchResult, LaborAssessment])
def test_llm_contracts_are_strict_compatible(model: type[BaseModel]):
    schema = model.model_json_schema()
    objects = list(_walk_objects(schema))
    assert objects
    for obj in objects:
        assert obj.get("additionalProperties") is False, obj.get("title")
        props = set(obj.get("properties", {}))
        assert set(obj.get("required", [])) == props, f"{obj.get('title')}: все поля должны быть обязательными"
    assert "$ref" not in str(schema.get("properties", {})) or "$defs" in schema


# --- Агент 3: прайс и цены ------------------------------------------------------


def test_catalog_item_normalization():
    item = CatalogItem(brand=" IEK ", sku="MVA20-3-016-C", name="ВА47-29 3P C16", base_price="1 234,50", currency="руб")
    assert item.currency == "RUB"
    assert item.base_price == Decimal("1234.50")
    assert item.catalog_uid.startswith("k_")
    assert item.brand == "IEK"
    with pytest.raises(ValidationError):
        CatalogItem(brand="X", sku="Y", name="Z", base_price="-1")
    with pytest.raises(ValidationError):
        CatalogItem(brand="X", sku="Y", name="Z", base_price="10", currency="XXXX")


def test_priced_item_pack_quantity():
    ferrules = CatalogItem(brand="КВТ", sku="НШВИ 1,5-8", name="Наконечник НШВИ 1,5-8 (уп. 1000 шт.)",
                           base_price="250", currency="ILS", unit=UnitOfMeasure.PACK, pack_quantity=1000)
    base = EngineeringItem(category=ComponentCategory.WIRE_FERRULE, name="НШВИ 1,5", quantity=1500)
    priced = PricedItem.from_engineering(
        base,
        candidates=[],
        match=MatchResult(match_type=MatchType.EXACT_SPECS, selected=ferrules, confidence=0.9, decided_by="rule"),
        unit_price_base=Decimal("250"),
    )
    assert priced.purchase_quantity == 2
    assert priced.line_total_base == Decimal("500.00")
    assert priced.sku == "НШВИ 1,5-8"
    assert priced.uid == base.uid


def test_match_result_consistency():
    with pytest.raises(ValidationError):
        MatchResult(match_type=MatchType.ANALOG, selected=None)


# --- Агент 4: итоги КП ----------------------------------------------------------


def test_estimate_totals():
    settings = EstimateSettings(
        base_currency="ILS",
        material_markup_pct=Decimal("25"),
        labor_rate_per_hour=Decimal("50"),
        contingency_pct=Decimal("5"),
        vat_pct=Decimal("18"),
    )
    line = EstimateLine(
        position=1,
        item_uid="e1",
        name="Автомат",
        category=ComponentCategory.CIRCUIT_BREAKER,
        quantity=Decimal("10"),
        purchase_unit_price=Decimal("100"),
        markup_pct=Decimal("25"),
        labor_hours_per_unit=Decimal("0.5"),
        labor_rate=Decimal("50"),
    )
    assert line.sale_unit_price == Decimal("125.00")
    assert line.labor_cost == Decimal("250.00")
    totals = EstimateTotals.compute([line], settings, overhead_hours=Decimal("2"))
    assert totals.materials_purchase == Decimal("1000.00")
    assert totals.materials_sale == Decimal("1250.00")
    assert totals.labor_hours == Decimal("7.00")
    assert totals.labor_cost == Decimal("350.00")
    assert totals.contingency_amount == Decimal("80.00")
    assert totals.subtotal_ex_vat == Decimal("1680.00")
    assert totals.vat_amount == Decimal("302.40")
    assert totals.total_inc_vat == Decimal("1982.40")
    assert totals.materials_margin_pct == Decimal("20.0")


def test_estimate_settings_rates():
    s = EstimateSettings(base_currency="ils", exchange_rates={"usd": "3.70", "€": 4.05})
    assert s.rate_to_base("USD") == Decimal("3.70")
    assert s.rate_to_base("EUR") == Decimal("4.05")
    assert s.rate_to_base("ILS") == Decimal(1)
    with pytest.raises(KeyError):
        s.rate_to_base("RUB")


# --- стоимость и наблюдаемость ---------------------------------------------------


def test_compute_cost_known_and_unknown_models():
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)
    cost, estimated = compute_cost(usage, "claude-opus-4-6")
    assert cost == Decimal("30.000000") and not estimated
    cost, estimated = compute_cost(usage, "claude-sonnet-4-6")
    assert cost == Decimal("18.000000")
    cost, estimated = compute_cost(TokenUsage(cache_read_input_tokens=1_000_000), "claude-opus-5-5")
    assert cost == Decimal("0.200000")
    cost, estimated = compute_cost(usage, "some-future-model")
    assert estimated and cost == Decimal("30.000000")


def test_compute_cost_long_context_tier():
    short, _ = compute_cost(TokenUsage(input_tokens=50_000, output_tokens=1_000), "claude-haiku-5-5")
    long_, _ = compute_cost(TokenUsage(input_tokens=200_000, output_tokens=1_000), "claude-haiku-5-5")
    assert short == Decimal("0.005500")
    assert long_ == Decimal("0.102500")


def test_token_usage_from_api():
    class U:
        input_tokens = 10
        output_tokens = 5
        cache_creation_input_tokens = None
        cache_read_input_tokens = 3

    assert TokenUsage.from_api(U()).total_tokens == 18
    assert TokenUsage.from_api({"input_tokens": 1, "output_tokens": 2}).output_tokens == 2
    assert TokenUsage.from_api(None).total_tokens == 0


def test_pipeline_run_aggregates_cost():
    run = PipelineRun()
    assert set(run.stages) == set(PipelineStage)
    run.stage(PipelineStage.EXTRACTION).calls.append(
        LLMCallRecord(stage=PipelineStage.EXTRACTION, agent_name="extractor", model_requested="claude-opus-4-6",
                      usage=TokenUsage(input_tokens=100), cost_usd=Decimal("0.0005"))
    )
    run.stage(PipelineStage.MATCHING).calls.append(
        LLMCallRecord(stage=PipelineStage.MATCHING, agent_name="matcher", model_requested="claude-sonnet-4-6",
                      usage=TokenUsage(output_tokens=10), cost_usd=Decimal("0.00015"))
    )
    assert run.total_cost_usd == Decimal("0.000650")
    assert run.total_usage.total_tokens == 110
    dumped = run.model_dump(mode="json")
    assert dumped["stages"]["extraction"]["cost_usd"] == "0.000500"


# --- конфигурация -----------------------------------------------------------------


def test_settings_pdf_options_follow_model(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    s = Settings(_env_file=None, data_dir=tmp_path)
    legacy = s.pdf_options("claude-opus-4-6")
    modern = s.pdf_options("claude-opus-5-5")
    assert legacy.tile_side_px == 1072
    assert modern.tile_side_px == 1936
    assert legacy.fingerprint() != modern.fingerprint()
    assert s.default_estimate_settings().base_currency == "ILS"
    with pytest.raises(Exception, match="ANTHROPIC_API_KEY"):
        s.require_api_key()


def test_registry_consistency():
    for model_id, profile in MODEL_REGISTRY.items():
        assert profile.model_id == model_id
        assert profile.cache_read_usd_per_mtok < profile.input_usd_per_mtok < profile.output_usd_per_mtok
        assert profile.vision_tile_side_px ** 2 <= profile.vision_max_pixels
    assert get_model_profile("claude-opus-4-6[1m]")[1] is True


def test_artifacts_round_trip_through_json():
    """Артефакты этапов сохраняются в JSON и загружаются обратно без потерь."""
    from specflow.schemas import ValidatedEngineeringBOM

    extraction = VisionPageExtraction.model_validate(LLM_PAGE_JSON)
    bom = ExtractedRawBOM(run_id="rt")
    bom.add_page_result(document_id="d", page_number=1, extraction=extraction)
    restored = ExtractedRawBOM.model_validate_json(bom.model_dump_json())
    assert restored.components[0].tags == bom.components[0].tags
    assert restored.component_count == 1

    validated = ValidatedEngineeringBOM(
        run_id="rt", items=[EngineeringItem.from_extracted(c) for c in bom.components]
    )
    again = ValidatedEngineeringBOM.model_validate_json(validated.model_dump_json())
    assert again.item_count == 1 and again.items[0].needs_review is False

    run = PipelineRun()
    assert PipelineRun.model_validate_json(run.model_dump_json()).run_id == run.run_id
