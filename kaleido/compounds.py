class Compound(object):
    """Represents a compound a biologist would store/register"""
    def __init__(self, id, state=None, props=None):
        self._id = id
        if props:
            self.load(props)
        else:
            self.state = state
            self.plate = []

    def load(self, props):
        self.state = props['state']
        self.plate = props['plate.well']

    # Return all of the properties of a compound
    def __todict__(self):
        return {'state': self.state, 'plate.well': self.plate}