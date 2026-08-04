"""Tests for SceneConceptExtractor."""

from ai_content_studio.assets.concept_extractor import SceneConceptExtractor
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.shared.models import Scene
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene_concept import SceneConcept

_SPANISH_NARRATION = (
    "Hubo un momento en que decidiste que llorar no valía la pena. "
    "No fue una decisión grande. Fue silenciosa, casi sin darte cuenta."
)

_VISUAL_PROMPT = (
    "Extreme close-up of a child's hand resting on a wooden floor, "
    "fingers slightly curled. Warm amber light from a low window. "
    "The rest of the frame is dark and out of focus."
)


def _make_scene(
    narration: str = _SPANISH_NARRATION,
    visual_prompt: str = _VISUAL_PROMPT,
    emotion: Emotion = Emotion.GRIEF,
) -> Scene:
    return Scene(
        order=1,
        narration=narration,
        visual_prompt=visual_prompt,
        emotion=emotion,
        duration_seconds=7.0,
    )


# --- extraction ---

def test_extract_returns_scene_concept() -> None:
    extractor = SceneConceptExtractor()
    result = extractor.extract(_make_scene())
    assert isinstance(result, SceneConcept)


def test_extract_preserves_emotion() -> None:
    extractor = SceneConceptExtractor()
    for emotion in Emotion:
        concept = extractor.extract(_make_scene(emotion=emotion))
        assert concept.emotion == emotion


def test_concepts_are_non_empty_for_visual_prompt() -> None:
    extractor = SceneConceptExtractor()
    concept = extractor.extract(_make_scene())
    assert len(concept.concepts) > 0


def test_concepts_come_from_visual_prompt_not_narration() -> None:
    extractor = SceneConceptExtractor()
    concept = extractor.extract(_make_scene())
    # Spanish narration words must not appear in concepts
    spanish_words = {"hubo", "momento", "decidiste", "llorar", "valía", "decisión",
                     "grande", "silenciosa", "darte", "cuenta"}
    concept_words = {w.lower() for w in " ".join(concept.concepts).split()}
    assert concept_words.isdisjoint(spanish_words)


def test_narration_words_never_in_query() -> None:
    extractor = SceneConceptExtractor()
    builder = SearchQueryBuilder()
    scene = _make_scene()
    concept = extractor.extract(scene)
    query = builder.build(concept)
    spanish_words = ["hubo", "decidiste", "llorar", "silenciosa", "darte"]
    for word in spanish_words:
        assert word not in query


def test_visual_focus_detected_for_close_up() -> None:
    extractor = SceneConceptExtractor()
    concept = extractor.extract(_make_scene(visual_prompt="Extreme close-up of hands in light."))
    assert concept.visual_focus == "close-up"


def test_visual_focus_detected_for_wide_shot() -> None:
    extractor = SceneConceptExtractor()
    concept = extractor.extract(_make_scene(visual_prompt="Wide shot of an empty street at dusk."))
    assert concept.visual_focus == "wide"


def test_visual_focus_none_when_no_shot_type() -> None:
    extractor = SceneConceptExtractor()
    concept = extractor.extract(_make_scene(visual_prompt="Rain falling on a wooden table."))
    assert concept.visual_focus is None


def test_empty_visual_prompt_returns_empty_concepts() -> None:
    extractor = SceneConceptExtractor()
    concept = extractor.extract(_make_scene(visual_prompt=""))
    assert concept.concepts == []


def test_extraction_is_deterministic() -> None:
    extractor = SceneConceptExtractor()
    scene = _make_scene()
    assert extractor.extract(scene) == extractor.extract(scene)


# --- concepts preserved in query ---

def test_extracted_concepts_appear_in_query() -> None:
    extractor = SceneConceptExtractor()
    builder = SearchQueryBuilder()
    scene = _make_scene(visual_prompt="Rain falling on a wooden table near a candle.")
    concept = extractor.extract(scene)
    query = builder.build(concept)
    assert any(c in query for c in concept.concepts)


# --- multi-emotion coverage ---

def test_extractor_works_across_all_emotions() -> None:
    extractor = SceneConceptExtractor()
    for emotion in Emotion:
        concept = extractor.extract(_make_scene(emotion=emotion))
        assert concept.emotion == emotion
        assert isinstance(concept.concepts, list)
