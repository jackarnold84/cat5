import json


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            return round(obj, 4)
        return super().default(obj)

    def encode(self, obj):
        def round_floats(item):
            if isinstance(item, float):
                return round(item, 4)
            elif isinstance(item, dict):
                return {k: round_floats(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [round_floats(i) for i in item]
            return item

        return super().encode(round_floats(obj))
