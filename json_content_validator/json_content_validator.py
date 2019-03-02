import inspect
import itertools

from json_content_validator.validators import ValidationStop, ValidationError

default_messages = {
    'required': 'Field is required',
    'email': 'Invalid email value',
    'regex': 'Invalid input value',
    'any_of': 'Invalid value, must be one of: ({})s',
    'number_range_min': 'Number must be at least ({})s',
    'number_range_max': 'Number must be at most ({})s.',
    'number_range_between': 'Number must be between %(min)s and %(max)s.',
    'uuid': 'Invalid UUID value',
    'url': 'Invalid URL value',
    'length_min': 'Field must be at least {} character/s long',
    'length_max': 'Field cannot be longer than {} character/s',
    'length_exact': 'Field must be exactly {} character/s long',
    'length_between': 'Field must be between {} and {} characters long',
}

class BaseKind(object):
    """
    BaseKind base class """
    errors = tuple()
    process_errors = tuple()
    validators = tuple()
    data = None
    __type = 'any'

    def __init__(self, name, validators=None, messages=None):
        self.name = name
        self.check_validators(validators)
        self.validators = validators or self.validators
        self._messages = messages

    @classmethod
    def check_validators(cls, validators):
        if not validators:
            return

        for validator in validators:
            if not callable(validator):
                raise TypeError(
                    f"{validator} is not a valid validator because "
                    "it is not callable"
                )

            if inspect.isclass(validator):
                raise TypeError(
                    f"{validator} is not a valid validator because "
                    "it is a class, it should be an instance"
                )

    def gettext(self, string):
        """
        Get a translation for the given message.

        This proxies for the internal translations object.

        :param string: A unicode string to be translated.
        :return: A unicode string which is the translated output.
        """
        return self._messages.get(string, 'No error message defined')

    def validate(self, json_data):
        """
        Validates the json and returns True or False. 
        `self.errors` will contain any errors raised during validation. """
        try:
            self.process_json(json_data)
        except ValueError as e:
            # self.process_errors.append(e.args[0])
            self.process_errors = [e.args[0]]

        self.errors = list(self.process_errors)

        # Run validators
        if not self.errors:
            chain = itertools.chain(self.validators)
            self._run_validation_chain(chain)

        return len(self.errors) == 0

    def _run_validation_chain(self, validators):
        """
        Run a validation chain, stopping if any validator raises ValidationStop. """
        for validator in validators:
            try:
                validator(self)
            except ValidationStop as e:
                # print('ValidationStop')
                if e.args and e.args[0]:
                    self.errors.append(e.args[0])
                break
            except ValueError as e:
                # print('ValueError')
                self.errors.append(e.args[0])
            except Exception as e:
                print(f'Some Exception {e.args[0]}')

    @property
    def type(self):
        return self.__type

class StringKind(BaseKind):

    __type = 'string'
    
    def process_json(self, json_data):
        value = json_data.get(self.name, None)
        if value:
            try:
                self.data = str(value)
            except ValueError:
                self.data = None
                raise ValueError("Not a valid string value")

class IntegerKind(BaseKind):

    __type = 'integer'
    
    def process_json(self, json_data):
        value = json_data.get(self.name, None)
        if value:
            try:
                self.data = int(value)
            except ValueError:
                self.data = None
                raise ValueError("Not a valid integer value")
                # raise ValueError(self.gettext("Not a valid integer value"))

class FloatKind(BaseKind):

    __type = 'float'
    
    def process_json(self, json_data):
        value = json_data.get(self.name, None)
        if value:
            try:
                self.data = float(value)
            except ValueError:
                self.data = None
                raise ValueError("Not a valid float value")

class AnyKind(BaseKind):

    def process_json(self, json_data):
        value = json_data.get(self.name, None)
        if value:
            self.data = value

class Validator():

    def __init__(self, schema):
        self._errors = None
        self._schema = schema

    def validate(self, json_data):
        """
        Validates the schema by calling `validate` on each item. """
        self._errors = None
        success = True
        for item in self._schema:
            if not item.validate(json_data):
                success = False

        return success

    @property
    def errors(self):
        if self._errors is None:
            self._errors = {i.name: i.errors for i in self._schema if i.errors}
        
        return self._errors

class JSONContentValidator():

    def __init__(self, messages=default_messages):
        self._messages = messages

    def schema(self, schema):
        return Validator(schema=schema)

    def string(self, name, validators):
        return StringKind(name, validators, self._messages)

    def integer(self, name, validators):
        return IntegerKind(name, validators, self._messages)

    def float(self, name, validators):
        return FloatKind(name, validators, self._messages)

    def any(self, name, validators):
        return AnyKind(name, validators, self._messages)

'''
class JSONContentValidator():

    def __init__(self, schema):
        self._errors = None
        self._schema = schema

    def validate(self, json_data):
        """
        Validates the schema by calling `validate` on each item. """
        self._errors = None
        success = True
        for item in self._schema:
            if not item.validate(json_data):
                success = False

        return success

    @property
    def errors(self):
        if self._errors is None:
            self._errors = {i.name: i.errors for i in self._schema if i.errors}
        
        return self._errors

    @classmethod
    def string(cls, name, validators):
        return StringKind(name, validators, messages=default_messages)

    @classmethod
    def integer(cls, name, validators):
        return IntegerKind(name, validators, messages=default_messages)

    @classmethod
    def float(cls, name, validators):
        return FloatKind(name, validators, messages=default_messages)

    @classmethod
    def any(cls, name, validators):
        return AnyKind(name, validators, messages=default_messages)
'''