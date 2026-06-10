class LabelFormatter:

    def __init__(self, template):
        self.template = template

    def format(self, branch):
        return self.template.format(**branch.metadata)
