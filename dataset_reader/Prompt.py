class Prompt:
    def __init__(self, expectedIntention, question) -> None:
        self.expectedIntention = expectedIntention
        self.question = question

    def checkIntention(self, actualIntention) -> bool:
        return self.expectedIntention == actualIntention