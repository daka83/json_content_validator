import re
import uuid
import string
from urllib.parse import urlparse

__all__ = (
    "Required",
    "Length",
    "Email",
    "Regex",
    "AnyOf",
    "NumberRange",
    "Optional",
    "UUID",
    "URL",
    "ValidationError",
    "ValidationStop",
)

email_re = '^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'

class ValidationError(ValueError):
    """
    Raised when a validator fails to validate its input.
    """

    def __init__(self, message="", *args, **kwargs):
        ValueError.__init__(self, message, *args, **kwargs)

class ValidationStop(Exception):
    """
    Causes the validation chain to stop.

    If ValidationStop is raised, no more validators in the validation chain are
    called. If raised with a message, the message will be added to the errors
    list.
    """

    def __init__(self, message="", *args, **kwargs):
        Exception.__init__(self, message, *args, **kwargs)

class Required(object):
    """
    Validates that input was provided for this field.

    Note there is a distinction between this and DataRequired in that
    InputRequired looks that form-input data was provided, and DataRequired
    looks at the post-coercion data.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, field):
        if not field.data:
            if self.message is None:
                message = field.gettext('required')
            else:
                message = self.message

            field.errors[:] = []
            raise ValidationStop(message)

class Length(object):
    """
    Validates the length of a string.

    :param min:
        The minimum required length of the string. If not provided, minimum
        length will not be checked.
    :param max:
        The maximum length of the string. If not provided, maximum length
        will not be checked.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated using `%(min)d` and `%(max)d` if desired. Useful defaults
        are provided depending on the existence of min and max.
    """

    def __init__(self, min=-1, max=-1, message=None):
        assert (
            min != -1 or max != -1
        ), "At least one of `min` or `max` must be specified."
        assert max == -1 or min <= max, "`min` cannot be more than `max`."
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, field):

        field_data = field.data
        if field.type != 'string':
            try:
                field_data = str(field.data)
            except Exception as e:
                raise ValidationError('Value can not be converted to string')

        length = field_data and len(field_data) or 0
        if length < self.min or self.max != -1 and length > self.max:
            message = self.message
            if message is None:
                if self.max == -1:
                    message = field.gettext('length_min').format(self.min)
                elif self.min == -1:
                    message = field.gettext('length_max').format(self.max)
                elif self.min == self.max:
                    message = field.gettext('length_exact').format(self.max)
                else:
                    message = field.gettext('length_between').format(self.min, self.max)

            raise ValidationError(
                message % dict(min=self.min, max=self.max, length=length)
            )

class Email(object):
    """
    Validates the field against a user provided regexp.

    :param regex:
        The regular expression string to use. Can also be a compiled regular
        expression pattern.
    :param flags:
        The regexp flags to use, for example re.IGNORECASE. Ignored if
        `regex` is not a string.
    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        self.regex = re.compile(email_re)
        self.message = message

    def __call__(self, field, message=None):
        match = self.regex.match(field.data or "")
        if not match:
            if message is None:
                if self.message is None:
                    message = field.gettext("email")
                else:
                    message = self.message

            raise ValidationError(message)

        return match

class Regex(object):
    """
    Validates the field against a user provided regexp.

    :param regex:
        The regular expression string to use. Can also be a compiled regular
        expression pattern.
    :param flags:
        The regexp flags to use, for example re.IGNORECASE. Ignored if
        `regex` is not a string.
    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, regex, flags=0, message=None):
        if isinstance(regex, str):
            regex = re.compile(regex, flags)
        self.regex = regex
        self.message = message

    def __call__(self, field, message=None):
        match = self.regex.match(field.data or "")
        if not match:
            if message is None:
                if self.message is None:
                    message = field.gettext("regex")
                else:
                    message = self.message

            raise ValidationError(message)
        return match

class AnyOf(object):
    """
    Compares the incoming data to a sequence of valid inputs.

    :param values:
        A sequence of valid inputs.
    :param message:
        Error message to raise in case of a validation error. `%(values)s`
        contains the list of values.
    :param values_formatter:
        Function used to format the list of values in the error message.
    """

    def __init__(self, values, message=None):
        self.values = values
        self.message = message

    def __call__(self, field):
        if field.data not in self.values:
            message = self.message
            if message is None:
                message = field.gettext('anyOf').format(self.values)

            raise ValidationError(message)

class NumberRange(object):
    """
    Validates that a number is of a minimum and/or maximum value, inclusive.
    This will work with any comparable number type, such as floats and
    decimals, not just integers.

    :param min:
        The minimum required value of the number. If not provided, minimum
        value will not be checked.
    :param max:
        The maximum value of the number. If not provided, maximum value
        will not be checked.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated using `%(min)s` and `%(max)s` if desired. Useful defaults
        are provided depending on the existence of min and max.
    """

    def __init__(self, min=None, max=None, message=None):
        self.min = min
        self.max = max
        self.message = message

    def __call__(self, field):
        data = field.data
        if (
            data is None
            or (self.min is not None and data < self.min)
            or (self.max is not None and data > self.max)
        ):
            message = self.message
            if message is None:
                # we use %(min)s interpolation to support floats, None, and
                # Decimals without throwing a formatting exception.
                if self.max is None:
                    message = field.gettext('number_range_max').format(self.max)
                elif self.min is None:
                    message = field.gettext('number_range_min').format(self.min)
                else:
                    message = field.gettext('number_range_between').format(self.min, self.max)

            raise ValidationError(message)

class Optional(object):
    """
    Allows empty input and stops the validation chain from continuing.

    If input is empty, also removes prior errors (such as processing errors)
    from the field.

    :param strip_whitespace:
        If True (the default) also stop the validation chain on input which
        consists of only whitespace.
    """

    def __call__(self, field):
        if not field.data:
            field.errors[:] = []
            raise ValidationStop()

class UUID(object):
    """
    Validates a UUID.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, field):
        message = self.message
        if message is None:
            message = field.gettext('uuid')
        try:
            uuid.UUID(field.data)
        except ValueError:
            raise ValidationError(message)

class URL(object):
    """
    Simple regexp based url validation. Much like the email validator, you
    probably want to validate the url later by other means if the url must
    resolve.

    :param require_tld:
        If true, then the domain-name portion of the URL must contain a .tld
        suffix.  Set this to false if you want to allow domains like
        `localhost`.
    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, field, message=None):
        try:
            parts = urlparse(field.data)
            assert all([parts.scheme, parts.netloc])
            assert parts.scheme in ['http', 'https']
        except Exception as e:
            if message is None:
                if self.message is None:
                    message = field.gettext('url')
                else:
                    message = self.message

            raise ValidationError(message)

        return True
