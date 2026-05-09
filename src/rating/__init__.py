"""Monza 2024 車手評分系統。"""

from importlib import import_module

__all__ = [
    'build_rating_features',
    'get_driver_rating_features',
    'build_rating_leaderboard',
    'get_driver_rating',
    'load_rating_leaderboard',
    'score_rating_features',
]


def __getattr__(name):
    if name in {'build_rating_features', 'get_driver_rating_features'}:
        module = import_module('src.rating.features')
        return getattr(module, name)
    if name in {'build_rating_leaderboard', 'get_driver_rating', 'load_rating_leaderboard'}:
        module = import_module('src.rating.leaderboard')
        return getattr(module, name)
    if name == 'score_rating_features':
        module = import_module('src.rating.scoring')
        return getattr(module, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
