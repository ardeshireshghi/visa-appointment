class WebForm:

    def __init__(self, action_url, form_data={}, **kwargs):
        self._action_url = action_url
        self._form_data = form_data
        for key, value in kwargs.items():
            setattr(self, '_' + key, value)

    def handler(self, handler = None):
        if (handler):
            self._handler = handler

        return self._handler

    def submit(self):
        self._headers = self._headers if hasattr(self, '_headers') else {}
        try:
            res = self.handler().post(
                url=self._action_url,
                data=self._form_data,
                headers=self._headers
            )

            self.response(res)

            return self
        except Exception as e:
            self.error(e)
            raise e

    def response(self, response = None):
        if (response):
            self._response = response

        return self._response

    def error(self, submit_error = None):
        if (submit_error):
            self._submit_error = submit_error

        return self._submit_error
