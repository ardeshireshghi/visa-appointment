class WebPage:

    def __init__(self, url, **kwargs):
        self._url = url
        for key, value in kwargs.items():
            setattr(self, '_' + key, value)

    def set_handler(self, handler):
        self._handler = handler

    def get_handler(self):
        return self._handler

    def set_response(self, response):
        self._response = response

    def get_response(self):
        return self._response if hasattr(self, '_response') else None

    def content(self):
        try:
            if not self.get_response():
                print "Fetching page: %s" % (self._url)
                self.set_response(self.get_handler().get(self._url))

            return self.get_response().text

        except Exception as e:
            self.error = e
            raise e
