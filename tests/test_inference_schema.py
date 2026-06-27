from apps.inference.src.main import FeatureVector


def test_feature_vector_accepts_minimum_payload():
    row = FeatureVector(
        mean_elevation=1.0,
        min_elevation=0.5,
        max_elevation=2.0,
        std_elevation=0.1,
        mean_slope=0.01,
        max_slope=0.02,
        mean_aspect=90.0,
        relief=1.5,
        roughness=0.2,
    )
    assert row.mean_elevation == 1.0
