class OpenAI:
    def __init__(self, *args, **kwargs):
        pass

    class responses:
        @staticmethod
        def create(*args, **kwargs):
            return type('obj', (object,), {'output': type('o', (object,), {'text': ''})})
