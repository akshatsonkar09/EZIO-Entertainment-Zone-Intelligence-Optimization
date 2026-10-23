import re
import contractions
import nltk

class Text_Normalization:
    def normalize(self, text):
        text = self.expand_contractions(text)
        text = self.lowercase(text)
        text = self.remove_spec_char(text)
        text = self.removewhitespace(text)
        return text

    def removewhitespace(self, text):
        text = " ".join(text.split())
        return text

    def lowercase(self,text):
        text = text.lower()
        return text

    def remove_spec_char(self,text):
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return text

    def expand_contractions(self, text):
        text = contractions.fix(text)
        return text

    
    