class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
    class _Responses:
        def create(self, *args, **kwargs):
            class _Resp:
                # mimic structure: resp.output[0].content[0].text
                output = []
            return _Resp()
    @property
    def responses(self):
        return self._Responses()
