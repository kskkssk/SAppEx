import re


class Extraction:
    def __init__(self):
        # self.model = model
        self.pattern_abs = re.compile(r"abstract\s*(.*)", re.DOTALL | re.IGNORECASE)
        self.pattern_key = re.compile(r"keywords\s*(.*)", re.DOTALL | re.IGNORECASE)
        self.pattern_int = re.compile(r"(?:\d*\s*\.?\s*)?(?:introduction)\b\s*(.*)", re.DOTALL | re.IGNORECASE)
        self.pattern_back = re.compile(
            r"^(?!.*\s*abstract\s+)(?:\d*\s*\.?\s*)?(?:background|introduction and background)\b\s*(.*)",
            re.DOTALL | re.IGNORECASE)

    def get_structure(self, strings):
        begin, middle, end = None, None, None
        state = None

        for string in strings:
            match_abs = self.pattern_abs.search(string)
            match_key = self.pattern_key.search(string)
            match_int = self.pattern_int.search(string)
            match_back = self.pattern_back.search(string)

            if begin and middle and end:
                break

            if match_abs:
                begin = 'abstract'
                state = 'abstract'

            elif match_key:
                if state == 'abstract':
                    middle = 'keywords'
                elif state == 'introduction':
                    end = 'keywords'
                else:
                    middle = 'keywords' if not middle else middle
                state = 'keywords'

            elif match_int:
                if state == 'abstract':
                    middle = 'introduction'
                elif state == 'keywords':
                    end = 'introduction'
                else:
                    middle = middle or 'introduction'
                state = 'introduction'

        return begin, middle, end

    def get_text(self, text, strings):
        abstract = None
        keywords = None

        match_abs = self.pattern_abs.search(text)
        match_key = self.pattern_key.search(text)
        match_int = self.pattern_int.search(text)

        #match_back = self.pattern_back.search(text)
        begin, middle, end = self.get_structure(strings)
        print(begin, middle, end)
        if begin == 'abstract' and match_abs:
            if middle == 'keywords' and match_key:
                abstract = text[match_abs.start():match_key.start()]
            elif end == 'introduction' and match_int:
                abstract = text[match_abs.start():match_int.start()]

        if middle == 'keywords' and match_key and end == 'introduction' and match_int:
            keywords = text[match_key.start():match_int.start()]
            # introduction = text[match_int.start():]  # Assuming introduction starts from match_int.end()

        return abstract, keywords


def preprocess(text):
    lower_text = text.lower()
    strings = lower_text.split('\n')
    return strings
