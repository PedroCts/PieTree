from .rules import StyleRule


class StyleResolver:

    def __init__(self, stylesheet):
        self.stylesheet = stylesheet

    def resolve(self, obj, context=None) -> StyleRule:
        computed = StyleRule()
        
        for selector_group, styles in self.stylesheet.rules:

            match = any(
                selector.match(obj)
                for selector in selector_group
            )

            if not match:
                continue
            
            for style in styles:
                    for field in style.items():
                        value = getattr(style, field)
                        if value is not None:
                            setattr(computed, field, value)
        return computed